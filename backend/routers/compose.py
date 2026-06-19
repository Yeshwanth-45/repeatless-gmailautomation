from fastapi import APIRouter, HTTPException

from db.supabase_client import supabase
from models.schemas import ComposeRequest, ReplyRequest, SendEmailRequest, SendReplyRequest
from services import gemini_service, gmail_service

router = APIRouter()


@router.post("/draft")
def draft_email(body: ComposeRequest) -> dict:
    """Generate a draft email using Gemini AI."""
    try:
        result = gemini_service.draft_email(prompt=body.prompt)
        return {"subject": result.get("subject", "Draft"), "body": result.get("body", "")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to draft email: {str(e)}")


@router.post("/send")
def send_email(body: SendEmailRequest) -> dict:
    """Send an email via Gmail API."""
    try:
        # Get user tokens
        user_result = supabase.table("users").select("*").eq("id", body.user_id).execute()
        if not user_result.data or len(user_result.data) == 0:
            raise HTTPException(status_code=404, detail="User not found")

        user = user_result.data[0]
        service = gmail_service.get_gmail_service(
            access_token=user["gmail_access_token"],
            refresh_token=user["gmail_refresh_token"],
            token_expiry=user.get("token_expiry"),
        )

        sent = gmail_service.send_email(
            gmail_service=service,
            to=body.to,
            subject=body.subject,
            body=body.body,
        )

        return {"status": "sent", "message_id": sent.get("id", "")}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


@router.post("/reply/draft")
def draft_reply(body: ReplyRequest) -> dict:
    """Generate a draft reply using thread context and Gemini AI."""
    try:
        # Fetch all messages in the thread
        emails_result = supabase.table("emails").select("*").eq(
            "thread_id", body.thread_id
        ).order("received_at", desc=False).execute()

        if not emails_result.data:
            raise HTTPException(status_code=404, detail="Thread not found or has no messages")

        thread_messages = [
            {
                "sender": e.get("sender", ""),
                "body_text": e.get("body_text", ""),
                "snippet": e.get("snippet", ""),
                "subject": e.get("subject", ""),
            }
            for e in emails_result.data
        ]

        reply_body = gemini_service.draft_reply(
            prompt=body.prompt,
            thread_messages=thread_messages,
        )

        # Get in_reply_to and references from the last message
        last_message = emails_result.data[-1]
        in_reply_to = last_message.get("gmail_message_id", "")
        references = last_message.get("references_header", "")

        # Build references chain
        if in_reply_to and references:
            references = f"{references} <{in_reply_to}>"
        elif in_reply_to:
            references = f"<{in_reply_to}>"

        return {
            "body": reply_body,
            "in_reply_to": in_reply_to,
            "references": references,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to draft reply: {str(e)}")


@router.post("/reply/send")
def send_reply(body: SendReplyRequest) -> dict:
    """Send a reply email via Gmail API within a thread."""
    try:
        # Get user tokens
        user_result = supabase.table("users").select("*").eq("id", body.user_id).execute()
        if not user_result.data or len(user_result.data) == 0:
            raise HTTPException(status_code=404, detail="User not found")

        user = user_result.data[0]

        # Get thread info to get gmail_thread_id and reply headers
        thread_result = supabase.table("threads").select("*").eq("id", body.thread_id).execute()
        if not thread_result.data or len(thread_result.data) == 0:
            raise HTTPException(status_code=404, detail="Thread not found")

        thread = thread_result.data[0]
        gmail_thread_id = thread.get("gmail_thread_id", "")

        # Get the last email in thread for In-Reply-To and References
        last_email_result = supabase.table("emails").select("*").eq(
            "thread_id", body.thread_id
        ).order("received_at", desc=True).limit(1).execute()

        in_reply_to = ""
        references = ""

        if last_email_result.data and len(last_email_result.data) > 0:
            last_email = last_email_result.data[0]
            msg_id = last_email.get("gmail_message_id", "")
            in_reply_to = f"<{msg_id}>" if msg_id else ""
            existing_refs = last_email.get("references_header", "")
            references = f"{existing_refs} {in_reply_to}".strip() if existing_refs else in_reply_to

        service = gmail_service.get_gmail_service(
            access_token=user["gmail_access_token"],
            refresh_token=user["gmail_refresh_token"],
            token_expiry=user.get("token_expiry"),
        )

        sent = gmail_service.send_email(
            gmail_service=service,
            to=body.to,
            subject=body.subject,
            body=body.body,
            in_reply_to=in_reply_to,
            references=references,
            thread_id=gmail_thread_id,
        )

        return {"status": "sent", "message_id": sent.get("id", "")}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send reply: {str(e)}")
