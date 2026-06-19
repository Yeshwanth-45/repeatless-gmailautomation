import base64
import re
import time
from email.mime.text import MIMEText
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from db.supabase_client import supabase
import os


def exponential_backoff(func, max_retries: int = 5):
    """Decorator that retries a function on 429 or 500 HTTP errors with exponential backoff."""
    def wrapper(*args, **kwargs):
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except HttpError as e:
                status_code = e.resp.status if hasattr(e, 'resp') else 0
                if status_code in (429, 500) and attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    raise
        raise Exception(f"Max retries ({max_retries}) exceeded for {func.__name__}")
    return wrapper


def get_gmail_service(access_token: str, refresh_token: str, token_expiry: Optional[str] = None):
    """Build and return an authenticated Gmail API service object."""
    try:
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
        )

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Update the new token in Supabase users table
            result = supabase.table("users").select("id").eq(
                "gmail_access_token", access_token
            ).execute()
            if result.data and len(result.data) > 0:
                user_id = result.data[0]["id"]
                supabase.table("users").update({
                    "gmail_access_token": creds.token,
                    "token_expiry": creds.expiry.isoformat() if creds.expiry else None
                }).eq("id", user_id).execute()

        service = build("gmail", "v1", credentials=creds)
        return service
    except Exception as e:
        raise Exception(f"Failed to build Gmail service: {str(e)}")


def _get_body_from_parts(parts: list) -> dict:
    """Recursively extract text/plain and text/html body from message parts."""
    body_text = ""
    body_html = ""

    for part in parts:
        mime_type = part.get("mimeType", "")
        data = part.get("body", {}).get("data", "")

        if mime_type == "text/plain" and data:
            body_text = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        elif mime_type == "text/html" and data:
            body_html = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        elif part.get("parts"):
            nested = _get_body_from_parts(part["parts"])
            if not body_text and nested.get("body_text"):
                body_text = nested["body_text"]
            if not body_html and nested.get("body_html"):
                body_html = nested["body_html"]

    return {"body_text": body_text, "body_html": body_html}


def parse_message(message_data: dict) -> dict:
    """Extract all relevant fields from a Gmail API message resource."""
    try:
        headers = message_data.get("payload", {}).get("headers", [])
        header_map = {}
        for h in headers:
            name = h.get("name", "").lower()
            header_map[name] = h.get("value", "")

        subject = header_map.get("subject", "")
        sender = header_map.get("from", "")
        to_header = header_map.get("to", "")
        in_reply_to = header_map.get("in-reply-to", "")
        references_header = header_map.get("references", "")

        # Parse sender email from sender string
        sender_email = ""
        email_match = re.search(r"<(.+?)>", sender)
        if email_match:
            sender_email = email_match.group(1)
        elif re.match(r"^[^@]+@[^@]+\.[^@]+$", sender.strip()):
            sender_email = sender.strip()

        # Parse recipients
        recipients = [r.strip() for r in to_header.split(",") if r.strip()] if to_header else []

        # Extract body
        payload = message_data.get("payload", {})
        body_text = ""
        body_html = ""

        if payload.get("parts"):
            bodies = _get_body_from_parts(payload["parts"])
            body_text = bodies.get("body_text", "")
            body_html = bodies.get("body_html", "")
        else:
            data = payload.get("body", {}).get("data", "")
            if data:
                decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                mime_type = payload.get("mimeType", "")
                if mime_type == "text/plain":
                    body_text = decoded
                elif mime_type == "text/html":
                    body_html = decoded

        # If no plain text but have HTML, strip tags for a text version
        if not body_text and body_html:
            body_text = re.sub(r"<[^>]+>", "", body_html)
            body_text = re.sub(r"\s+", " ", body_text).strip()

        snippet = message_data.get("snippet", "")
        labels = message_data.get("labelIds", [])
        received_at = ""
        internal_date = message_data.get("internalDate")
        if internal_date:
            from datetime import datetime, timezone
            received_at = datetime.fromtimestamp(
                int(internal_date) / 1000, tz=timezone.utc
            ).isoformat()

        return {
            "gmail_message_id": message_data.get("id", ""),
            "gmail_thread_id": message_data.get("threadId", ""),
            "subject": subject,
            "sender": sender,
            "sender_email": sender_email,
            "recipients": recipients,
            "body_text": body_text,
            "body_html": body_html,
            "snippet": snippet,
            "received_at": received_at,
            "labels": labels,
            "in_reply_to": in_reply_to,
            "references_header": references_header,
        }
    except Exception as e:
        return {
            "gmail_message_id": message_data.get("id", ""),
            "gmail_thread_id": message_data.get("threadId", ""),
            "subject": "",
            "sender": "",
            "sender_email": "",
            "recipients": [],
            "body_text": "",
            "body_html": "",
            "snippet": "",
            "received_at": "",
            "labels": [],
            "in_reply_to": "",
            "references_header": "",
        }


def fetch_all_threads(gmail_service, user_id: str) -> list:
    """Fetch ALL threads from Gmail with full message data, processing in batches of 50."""
    all_threads = []
    page_token = None

    @exponential_backoff
    def list_threads(page_token=None):
        params = {"userId": "me", "maxResults": 100}
        if page_token:
            params["pageToken"] = page_token
        return gmail_service.users().threads().list(**params).execute()

    @exponential_backoff
    def get_thread(thread_id):
        return gmail_service.users().threads().get(
            userId="me", id=thread_id, format="full"
        ).execute()

    thread_ids = []
    while True:
        result = list_threads(page_token)
        threads = result.get("threads", [])
        thread_ids.extend([t["id"] for t in threads])
        
        # Stop early to avoid hitting Gmail rate limits (we only process 100 anyway)
        if len(thread_ids) >= 100:
            thread_ids = thread_ids[:100]
            break
            
        page_token = result.get("nextPageToken")
        if not page_token:
            break

    # Fetch full thread data in batches of 50
    for i in range(0, len(thread_ids), 50):
        batch = thread_ids[i:i + 50]
        for thread_id in batch:
            try:
                thread_data = get_thread(thread_id)
                messages = thread_data.get("messages", [])
                parsed_messages = [parse_message(msg) for msg in messages]
                all_threads.append({
                    "gmail_thread_id": thread_data.get("id", ""),
                    "messages": parsed_messages,
                })
            except Exception as e:
                continue
        if i + 50 < len(thread_ids):
            time.sleep(0.1)

    return all_threads


def fetch_incremental(gmail_service, user_id: str, history_id: str) -> dict:
    """Fetch only new messages since the given history_id."""
    new_messages = []
    new_history_id = history_id
    page_token = None

    @exponential_backoff
    def list_history(page_token=None):
        params = {
            "userId": "me",
            "startHistoryId": history_id,
            "historyTypes": ["messageAdded"],
        }
        if page_token:
            params["pageToken"] = page_token
        return gmail_service.users().history().list(**params).execute()

    @exponential_backoff
    def get_message(message_id):
        return gmail_service.users().messages().get(
            userId="me", id=message_id, format="full"
        ).execute()

    try:
        while True:
            result = list_history(page_token)
            new_history_id = result.get("historyId", history_id)
            history_records = result.get("history", [])

            for record in history_records:
                messages_added = record.get("messagesAdded", [])
                for msg_record in messages_added:
                    message_id = msg_record.get("message", {}).get("id")
                    if message_id:
                        try:
                            full_message = get_message(message_id)
                            parsed = parse_message(full_message)
                            new_messages.append(parsed)
                        except Exception:
                            continue

            page_token = result.get("nextPageToken")
            if not page_token:
                break
    except HttpError as e:
        if e.resp.status == 404:
            # History ID is too old, need full sync
            return {"messages": [], "history_id": None}
        raise

    return {"messages": new_messages, "history_id": new_history_id}


def send_email(
    gmail_service,
    to: str,
    subject: str,
    body: str,
    in_reply_to: Optional[str] = None,
    references: Optional[str] = None,
    thread_id: Optional[str] = None,
) -> dict:
    """Build and send an email via the Gmail API."""
    try:
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject

        if in_reply_to:
            message["In-Reply-To"] = in_reply_to
        if references:
            message["References"] = references

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        message_body = {"raw": raw}
        if thread_id:
            message_body["threadId"] = thread_id

        sent_message = (
            gmail_service.users()
            .messages()
            .send(userId="me", body=message_body)
            .execute()
        )
        return sent_message
    except Exception as e:
        raise Exception(f"Failed to send email: {str(e)}")
