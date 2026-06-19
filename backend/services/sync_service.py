import time
import logging

from db.supabase_client import supabase
from services import gmail_service, gemini_service, embedding_service, category_service

logger = logging.getLogger(__name__)

MAX_EMAILS_PER_SYNC = 100
DELAY_BETWEEN_AI_CALLS = 0.3


def _safe_categorize(subject, sender, snippet):
    try:
        return category_service.get_category(subject, sender, snippet)
    except Exception:
        return "Work/Professional"


def _safe_summarize(subject, sender, body_text):
    try:
        return gemini_service.summarize_email(subject, sender, body_text)
    except Exception:
        return ""


def _safe_summarize_thread(messages):
    try:
        return gemini_service.summarize_thread(messages)
    except Exception:
        return ""


def _embed_synced_email(email_id, user_id, msg, gmail_thread_id):
    try:
        body_text = (msg.get("body_text") or msg.get("snippet") or "").strip()
        if not email_id or not body_text:
            return 0
        return embedding_service.store_email_embeddings(
            email_id=email_id,
            user_id=user_id,
            body_text=body_text,
            metadata={
                "sender": msg.get("sender", ""),
                "sender_email": msg.get("sender_email", ""),
                "subject": msg.get("subject", ""),
                "received_at": msg.get("received_at", ""),
                "gmail_message_id": msg.get("gmail_message_id", ""),
                "gmail_thread_id": gmail_thread_id,
            },
        )
    except Exception as e:
        logger.error(f"Embedding failed for email {email_id}: {e}")
        return 0


def initial_sync(user_id: str) -> dict:
    try:
        user_result = supabase.table("users").select("*").eq("id", user_id).execute()
        if not user_result.data:
            raise Exception(f"User {user_id} not found")

        user = user_result.data[0]
        access_token = user.get("gmail_access_token")
        refresh_token = user.get("gmail_refresh_token")
        token_expiry = user.get("token_expiry")

        if not access_token or not refresh_token:
            raise Exception("User has no Gmail tokens. Please authenticate first.")

        gmail_svc = gmail_service.get_gmail_service(
            access_token, refresh_token, token_expiry
        )
        all_threads = gmail_service.fetch_all_threads(gmail_svc, user_id)
        all_threads = all_threads[:MAX_EMAILS_PER_SYNC]

        emails_synced = 0
        threads_synced = 0

        for thread_data in all_threads:
            try:
                gmail_thread_id = thread_data.get("gmail_thread_id", "")
                messages = thread_data.get("messages", [])
                if not messages:
                    continue

                first_message = messages[0]
                subject = first_message.get("subject", "")
                participants = list(set(
                    msg.get("sender_email", "")
                    for msg in messages if msg.get("sender_email")
                ))
                last_message_at = messages[-1].get("received_at", "") if messages else ""

                try:
                    thread_upsert = supabase.table("threads").upsert(
                        {
                            "user_id": user_id,
                            "gmail_thread_id": gmail_thread_id,
                            "subject": subject,
                            "participants": participants,
                            "last_message_at": last_message_at or None,
                            "message_count": len(messages),
                        },
                        on_conflict="gmail_thread_id,user_id",
                    ).execute()
                    thread_id = thread_upsert.data[0]["id"] if thread_upsert.data else None
                except Exception as e:
                    logger.error(f"Thread upsert failed: {e}")
                    continue

                first_category = "Work/Professional"

                for idx, msg in enumerate(messages):
                    try:
                        if idx > 0:
                            time.sleep(DELAY_BETWEEN_AI_CALLS)

                        category = _safe_categorize(
                            msg.get("subject", ""),
                            msg.get("sender", ""),
                            msg.get("snippet", ""),
                        )
                        if idx == 0:
                            first_category = category

                        summary = _safe_summarize(
                            msg.get("subject", ""),
                            msg.get("sender", ""),
                            msg.get("body_text", ""),
                        )

                        email_upsert = supabase.table("emails").upsert(
                            {
                                "user_id": user_id,
                                "thread_id": thread_id,
                                "gmail_message_id": msg.get("gmail_message_id", ""),
                                "gmail_thread_id": gmail_thread_id,
                                "subject": msg.get("subject", ""),
                                "sender": msg.get("sender", ""),
                                "sender_email": msg.get("sender_email", ""),
                                "recipients": msg.get("recipients", []),
                                "body_text": msg.get("body_text", ""),
                                "body_html": msg.get("body_html", ""),
                                "snippet": msg.get("snippet", ""),
                                "received_at": msg.get("received_at") or None,
                                "labels": msg.get("labels", []),
                                "category": category,
                                "summary": summary,
                                "in_reply_to": msg.get("in_reply_to", ""),
                                "references_header": msg.get("references_header", ""),
                                "is_read": "UNREAD" not in msg.get("labels", []),
                            },
                            on_conflict="gmail_message_id",
                        ).execute()

                        email_id = email_upsert.data[0]["id"] if email_upsert.data else None
                        if email_id:
                            _embed_synced_email(email_id, user_id, msg, gmail_thread_id)

                        emails_synced += 1

                    except Exception as e:
                        logger.error(f"Email processing failed: {e}")
                        continue

                try:
                    thread_summary = _safe_summarize_thread(messages)
                    supabase.table("threads").update({
                        "thread_summary": thread_summary,
                        "category": first_category,
                        "message_count": len(messages),
                    }).eq("id", thread_id).execute()
                except Exception:
                    pass

                threads_synced += 1

            except Exception as e:
                logger.error(f"Thread processing failed: {e}")
                continue

        try:
            profile = gmail_svc.users().getProfile(userId="me").execute()
            history_id = profile.get("historyId")
            if history_id:
                supabase.table("users").update({
                    "gmail_history_id": history_id,
                }).eq("id", user_id).execute()
        except Exception:
            pass

        return {
            "emails_synced": emails_synced,
            "threads_synced": threads_synced,
            "status": "completed",
        }

    except Exception as e:
        raise Exception(f"Initial sync failed: {str(e)}")


def incremental_sync(user_id: str) -> dict:
    try:
        user_result = supabase.table("users").select("*").eq("id", user_id).execute()
        if not user_result.data:
            raise Exception(f"User {user_id} not found")

        user = user_result.data[0]
        history_id = user.get("gmail_history_id")

        if not history_id:
            return initial_sync(user_id)

        access_token = user.get("gmail_access_token")
        refresh_token = user.get("gmail_refresh_token")
        token_expiry = user.get("token_expiry")

        if not access_token or not refresh_token:
            raise Exception("User has no Gmail tokens.")

        gmail_svc = gmail_service.get_gmail_service(
            access_token, refresh_token, token_expiry
        )
        incremental_result = gmail_service.fetch_incremental(
            gmail_svc, user_id, history_id
        )

        new_messages = incremental_result.get("messages", [])
        new_history_id = incremental_result.get("history_id")

        if new_history_id is None:
            return initial_sync(user_id)

        emails_synced = 0
        threads_synced = 0
        processed_thread_ids = set()

        for idx, msg in enumerate(new_messages):
            try:
                if idx > 0:
                    time.sleep(DELAY_BETWEEN_AI_CALLS)

                gmail_thread_id = msg.get("gmail_thread_id", "")

                category = _safe_categorize(
                    msg.get("subject", ""),
                    msg.get("sender", ""),
                    msg.get("snippet", ""),
                )

                summary = _safe_summarize(
                    msg.get("subject", ""),
                    msg.get("sender", ""),
                    msg.get("body_text", ""),
                )

                thread_result = supabase.table("threads").select("id").eq(
                    "gmail_thread_id", gmail_thread_id
                ).eq("user_id", user_id).execute()

                thread_id = None
                if thread_result.data:
                    thread_id = thread_result.data[0]["id"]
                else:
                    thread_insert = supabase.table("threads").insert({
                        "user_id": user_id,
                        "gmail_thread_id": gmail_thread_id,
                        "subject": msg.get("subject", ""),
                        "participants": [msg.get("sender_email", "")],
                        "last_message_at": msg.get("received_at") or None,
                        "category": category,
                        "message_count": 1,
                    }).execute()
                    thread_id = thread_insert.data[0]["id"] if thread_insert.data else None

                email_upsert = supabase.table("emails").upsert(
                    {
                        "user_id": user_id,
                        "thread_id": thread_id,
                        "gmail_message_id": msg.get("gmail_message_id", ""),
                        "gmail_thread_id": gmail_thread_id,
                        "subject": msg.get("subject", ""),
                        "sender": msg.get("sender", ""),
                        "sender_email": msg.get("sender_email", ""),
                        "recipients": msg.get("recipients", []),
                        "body_text": msg.get("body_text", ""),
                        "body_html": msg.get("body_html", ""),
                        "snippet": msg.get("snippet", ""),
                        "received_at": msg.get("received_at") or None,
                        "labels": msg.get("labels", []),
                        "category": category,
                        "summary": summary,
                        "in_reply_to": msg.get("in_reply_to", ""),
                        "references_header": msg.get("references_header", ""),
                        "is_read": "UNREAD" not in msg.get("labels", []),
                    },
                    on_conflict="gmail_message_id",
                ).execute()

                email_id = email_upsert.data[0]["id"] if email_upsert.data else None
                if email_id:
                    _embed_synced_email(email_id, user_id, msg, gmail_thread_id)

                emails_synced += 1

                if gmail_thread_id and gmail_thread_id not in processed_thread_ids:
                    processed_thread_ids.add(gmail_thread_id)
                    threads_synced += 1

            except Exception as e:
                logger.error(f"Incremental email failed: {e}")
                continue

        if new_history_id:
            supabase.table("users").update({
                "gmail_history_id": new_history_id,
            }).eq("id", user_id).execute()

        return {
            "emails_synced": emails_synced,
            "threads_synced": threads_synced,
            "status": "completed",
        }

    except Exception as e:
        raise Exception(f"Incremental sync failed: {str(e)}")