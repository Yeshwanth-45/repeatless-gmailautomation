from fastapi import APIRouter, HTTPException

from db.supabase_client import supabase
from models.schemas import SyncResponse
from services import sync_service

router = APIRouter()


@router.post("/{user_id}")
def sync_emails(user_id: str) -> SyncResponse:
    """Trigger email sync for a user. Uses incremental sync if history_id exists, otherwise full sync."""
    try:
        # Get user from Supabase
        user_result = supabase.table("users").select("id, gmail_history_id").eq("id", user_id).execute()

        if not user_result.data or len(user_result.data) == 0:
            raise HTTPException(status_code=404, detail="User not found")

        user = user_result.data[0]
        has_history_id = bool(user.get("gmail_history_id"))

        if has_history_id:
            result = sync_service.incremental_sync(user_id)
        else:
            result = sync_service.initial_sync(user_id)

        return SyncResponse(
            emails_synced=result.get("emails_synced", 0),
            threads_synced=result.get("threads_synced", 0),
            status=result.get("status", "completed"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")
