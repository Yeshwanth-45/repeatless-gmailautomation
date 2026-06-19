from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from db.supabase_client import supabase
from models.schemas import CategoryStats, EmailListResponse, EmailResponse

router = APIRouter()


@router.get("")
def list_emails(
    user_id: str = Query(..., description="User ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
) -> EmailListResponse:
    """List emails for a user with optional category filter and pagination."""
    try:
        offset = (page - 1) * limit

        # Build query for total count
        count_query = supabase.table("emails").select("id", count="exact").eq("user_id", user_id)
        if category:
            count_query = count_query.eq("category", category)
        count_result = count_query.execute()
        total = count_result.count if count_result.count is not None else 0

        # Build query for emails
        query = supabase.table("emails").select("*").eq("user_id", user_id)
        if category:
            query = query.eq("category", category)
        query = query.order("received_at", desc=True).range(offset, offset + limit - 1)
        result = query.execute()

        emails = []
        for e in (result.data or []):
            emails.append(EmailResponse(
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

        return EmailListResponse(emails=emails, total=total, page=page)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list emails: {str(e)}")


@router.get("/categories/stats")
def get_category_stats(
    user_id: str = Query(..., description="User ID"),
) -> list[CategoryStats]:
    """Get email count grouped by category for a user."""
    try:
        result = supabase.table("emails").select("category").eq("user_id", user_id).execute()

        if not result.data:
            return []

        # Count by category
        category_counts: dict[str, int] = {}
        for row in result.data:
            cat = row.get("category", "Uncategorized")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return [
            CategoryStats(category=cat, count=count)
            for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get category stats: {str(e)}")


@router.get("/{email_id}")
def get_email(email_id: str) -> EmailResponse:
    """Get a single email by ID with its summary."""
    try:
        result = supabase.table("emails").select("*").eq("id", email_id).execute()

        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=404, detail="Email not found")

        e = result.data[0]
        return EmailResponse(
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
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get email: {str(e)}")
