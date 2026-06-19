from fastapi import APIRouter, HTTPException

from db.supabase_client import supabase
from models.schemas import EmbedResponse
from services import embedding_service

router = APIRouter()


@router.post("/{user_id}", response_model=EmbedResponse)
def reembed_user_emails(user_id: str) -> EmbedResponse:
    """Re-chunk and re-embed all existing emails for a user."""
    try:
        user_result = supabase.table("users").select("id").eq("id", user_id).execute()
        if not user_result.data:
            raise HTTPException(status_code=404, detail="User not found")

        result = embedding_service.reembed_user_emails(user_id)
        return EmbedResponse(
            emails_processed=result["emails_processed"],
            chunks_created=result["chunks_created"],
            emails_skipped=result["emails_skipped"],
            errors=result["errors"],
            status=result["status"],
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Re-embed failed: {exc}") from exc
