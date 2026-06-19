from db.supabase_client import supabase
from services import gmail_service, gemini_service, embedding_service, category_service


def _embed_synced_email(
    email_id: str,
    user_id: str,
    msg: dict,
    gmail_thread_id: str,
) -> int:
    """Chunk and embed a synced email body (falls back to snippet)."""
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


def initial_sync(user_id: str) -> dict:
    """Perform a full sync of all Gmail threads for a user."""
    try:
        # Get user from Supabase
        user_result = supabase.table("users").select("*").eq("id", user_id).execute()
        if not user_result.data or len(user_result.data) == 0:
            raise Exception(f"User {user_id} not found")

        user = user_result.data[0]
        access_token = user.get("gmail_access_token")
        refresh_token = user.get("gmail_refresh_token")
        token_expiry = user.get("token_expiry")

        if not access_token or not refresh_token:
            raise Exception("User has no Gmail tokens. Please authenticate first.")

        # Build Gmail service
        gmail_svc = gmail_service.get_gmail_service(access_token, refresh_token, token_expiry)

        # Fetch all threads
        all_threads = gmail_service.fetch_all_threads(gmail_svc, user_id)

        emails_synced = 0
        threads_synced = 0

        for thread_data in all_threads:
            try:
                gmail_thread_id = thread_data.get("gmail_thread_id", "")
                messages = thread_data.get("messages", [])

                if not messages:
                    continue

                # Determine subject from first message, participants from all messages
                first_message = messages[0]
                subject = first_message.get("subject", "")
                participants = list(set(
                    msg.get("sender_email", "") for msg in messages if msg.get("sender_email")
                ))

                # Determine last_message_at from the latest message
                last_message_at = messages[-1].get("received_at", "") if messages else ""

                # Upsert thread record
                thread_record = {
                    "user_id": user_id,
                    "gmail_thread_id": gmail_thread_id,
                    "subject": subject,
                    "participants": participants,
                    "last_message_at": last_message_at if last_message_at else None,
                    "message_count": len(messages),
                }

                thread_upsert = supabase.table("threads").upsert(
                    thread_record,
                    on_conflict="gmail_thread_id,user_id",
                ).execute()

                thread_id = thread_upsert.data[0]["id"] if thread_upsert.data else None

                first_category = "Work/Professional"

                # Process each message
                for idx, msg in enumerate(messages):
                    try:
                        # Categorize
                        category = category_service.get_category(
                            msg.get("subject", ""),
                            msg.get("sender", ""),
                            msg.get("snippet", ""),
                        )
                        if idx == 0:
                            first_category = category

                        # Summarize
                        summary = gemini_service.summarize_email(
                            msg.get("subject", ""),
                            msg.get("sender", ""),
                            msg.get("body_text", ""),
                        )

                        # Upsert email record
                        email_record = {
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
                            "received_at": msg.get("received_at") if msg.get("received_at") else None,
                            "labels": msg.get("labels", []),
                            "category": category,
                            "summary": summary,
                            "in_reply_to": msg.get("in_reply_to", ""),
                            "references_header": msg.get("references_header", ""),
                            "is_read": "UNREAD" not in msg.get("labels", []),
                        }

                        email_upsert = supabase.table("emails").upsert(
                            email_record,
                            on_conflict="gmail_message_id",
                        ).execute()

                        email_id = email_upsert.data[0]["id"] if email_upsert.data else None

                        if email_id:
                            _embed_synced_email(email_id, user_id, msg, gmail_thread_id)

                        emails_synced += 1
                    except Exception:
                        continue

                # Generate thread summary
                try:
                    thread_summary = gemini_service.summarize_thread(messages)
                    supabase.table("threads").update({
                        "thread_summary": thread_summary,
                        "category": first_category,
                        "message_count": len(messages),
                    }).eq("id", thread_id).execute()
                except Exception:
                    pass

                threads_synced += 1
            except Exception:
                continue

        # Get history_id from Gmail profile
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
    """Perform an incremental sync using Gmail history API."""
    try:
        # Get user with stored history_id
        user_result = supabase.table("users").select("*").eq("id", user_id).execute()
        if not user_result.data or len(user_result.data) == 0:
            raise Exception(f"User {user_id} not found")

        user = user_result.data[0]
        history_id = user.get("gmail_history_id")

        if not history_id:
            return initial_sync(user_id)

        access_token = user.get("gmail_access_token")
        refresh_token = user.get("gmail_refresh_token")
        token_expiry = user.get("token_expiry")

        if not access_token or not refresh_token:
            raise Exception("User has no Gmail tokens. Please authenticate first.")

        # Build Gmail service
        gmail_svc = gmail_service.get_gmail_service(access_token, refresh_token, token_expiry)

        # Fetch incremental changes
        incremental_result = gmail_service.fetch_incremental(gmail_svc, user_id, history_id)

        new_messages = incremental_result.get("messages", [])
        new_history_id = incremental_result.get("history_id")

        # If history_id is None, it means it's too old — do full sync
        if new_history_id is None:
            return initial_sync(user_id)

        emails_synced = 0
        threads_synced = 0
        processed_thread_ids = set()

        for msg in new_messages:
            try:
                gmail_thread_id = msg.get("gmail_thread_id", "")

                # Categorize
                category = category_service.get_category(
                    msg.get("subject", ""),
                    msg.get("sender", ""),
                    msg.get("snippet", ""),
                )

                # Summarize
                summary = gemini_service.summarize_email(
                    msg.get("subject", ""),
                    msg.get("sender", ""),
                    msg.get("body_text", ""),
                )

                # Check if thread exists
                thread_result = supabase.table("threads").select("id").eq(
                    "gmail_thread_id", gmail_thread_id
                ).eq("user_id", user_id).execute()

                thread_id = None
                if thread_result.data and len(thread_result.data) > 0:
                    thread_id = thread_result.data[0]["id"]
                else:
                    # Create thread record
                    thread_insert = supabase.table("threads").insert({
                        "user_id": user_id,
                        "gmail_thread_id": gmail_thread_id,
                        "subject": msg.get("subject", ""),
                        "participants": [msg.get("sender_email", "")],
                        "last_message_at": msg.get("received_at") if msg.get("received_at") else None,
                        "category": category,
                        "message_count": 1,
                    }).execute()
                    thread_id = thread_insert.data[0]["id"] if thread_insert.data else None

                # Upsert email record
                email_record = {
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
                    "received_at": msg.get("received_at") if msg.get("received_at") else None,
                    "labels": msg.get("labels", []),
                    "category": category,
                    "summary": summary,
                    "in_reply_to": msg.get("in_reply_to", ""),
                    "references_header": msg.get("references_header", ""),
                    "is_read": "UNREAD" not in msg.get("labels", []),
                }

                email_upsert = supabase.table("emails").upsert(
                    email_record,
                    on_conflict="gmail_message_id",
                ).execute()

                email_id = email_upsert.data[0]["id"] if email_upsert.data else None

                if email_id:
                    _embed_synced_email(email_id, user_id, msg, gmail_thread_id)

                emails_synced += 1

                # Track thread for summary update
                if gmail_thread_id and gmail_thread_id not in processed_thread_ids:
                    processed_thread_ids.add(gmail_thread_id)
                    threads_synced += 1

                    # Update thread summary
                    try:
                        thread_emails = supabase.table("emails").select("*").eq(
                            "gmail_thread_id", gmail_thread_id
                        ).eq("user_id", user_id).order("received_at").execute()

                        if thread_emails.data:
                            thread_messages = [
                                {
                                    "sender": e.get("sender", ""),
                                    "body_text": e.get("body_text", ""),
                                    "snippet": e.get("snippet", ""),
                                }
                                for e in thread_emails.data
                            ]
                            thread_summary = gemini_service.summarize_thread(thread_messages)
                            supabase.table("threads").update({
                                "thread_summary": thread_summary,
                                "message_count": len(thread_emails.data),
                                "last_message_at": thread_emails.data[-1].get("received_at"),
                            }).eq("id", thread_id).execute()
                    except Exception:
                        pass

            except Exception:
                continue

        # Update history_id
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
