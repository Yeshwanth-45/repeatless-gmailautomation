from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from db.supabase_client import supabase
from models.schemas import (
    EmailResponse,
    ThreadDetailResponse,
    ThreadListResponse,
    ThreadResponse,
)

router = APIRouter()


@router.get("")
def list_threads(
    user_id: str = Query(..., description="User ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
) -> ThreadListResponse:
    """List threads for a user with optional category filter and pagination."""
    try:
        offset = (page - 1) * limit

        # Count total
        count_query = supabase.table("threads").select("id", count="exact").eq("user_id", user_id)
        if category:
            count_query = count_query.eq("category", category)
        count_result = count_query.execute()
        total = count_result.count if count_result.count is not None else 0

        # Fetch threads
        query = supabase.table("threads").select("*").eq("user_id", user_id)
        if category:
            query = query.eq("category", category)
        query = query.order("last_message_at", desc=True).range(offset, offset + limit - 1)
        result = query.execute()

        threads = []
        for t in (result.data or []):
            threads.append(ThreadResponse(
                id=t.get("id", ""),
                user_id=t.get("user_id", ""),
                gmail_thread_id=t.get("gmail_thread_id"),
                subject=t.get("subject"),
                participants=t.get("participants"),
                last_message_at=str(t.get("last_message_at", "")),
                thread_summary=t.get("thread_summary"),
                category=t.get("category"),
                message_count=t.get("message_count"),
                created_at=str(t.get("created_at", "")),
            ))

        return ThreadListResponse(threads=threads, total=total, page=page)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list threads: {str(e)}")


@router.get("/{thread_id}")
def get_thread(thread_id: str) -> ThreadDetailResponse:
    """Get a thread with all its messages ordered by received_at ascending."""
    try:
        # Get thread info
        thread_result = supabase.table("threads").select("*").eq("id", thread_id).execute()

        if not thread_result.data or len(thread_result.data) == 0:
            raise HTTPException(status_code=404, detail="Thread not found")

        t = thread_result.data[0]

        # Get all emails in thread ordered by received_at ASC
        emails_result = supabase.table("emails").select("*").eq(
            "thread_id", thread_id
        ).order("received_at", desc=False).execute()

        messages = []
        for e in (emails_result.data or []):
            messages.append(EmailResponse(
                id=e.get("id", ""),
                user_id=e.get("user_id", ""),
                thread_id=e.get("thread_id"),
                gmail_message_id=e.get("gmail_message_id"),
                gmail_thread_id=e.get("gmail_thread_id"),
                subject=e.get("subject"),
                sender=e.get("sender"),
                sender_email=e.get("sender_email"),
                recipients=e.get("recipients"),
                body_text=e.get("body_text"),
                body_html=e.get("body_html"),
                snippet=e.get("snippet"),
                received_at=str(e.get("received_at", "")),
                labels=e.get("labels"),
                category=e.get("category"),
                summary=e.get("summary"),
                in_reply_to=e.get("in_reply_to"),
                references_header=e.get("references_header"),
                is_read=e.get("is_read"),
                created_at=str(e.get("created_at", "")),
            ))

        return ThreadDetailResponse(
            id=t.get("id", ""),
            user_id=t.get("user_id", ""),
            gmail_thread_id=t.get("gmail_thread_id"),
            subject=t.get("subject"),
            participants=t.get("participants"),
            last_message_at=str(t.get("last_message_at", "")),
            thread_summary=t.get("thread_summary"),
            category=t.get("category"),
            message_count=t.get("message_count"),
            created_at=str(t.get("created_at", "")),
            messages=messages,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get thread: {str(e)}")
