import threading

from fastapi import APIRouter, HTTPException

from db.supabase_client import supabase
from models.schemas import SyncResponse
from services import sync_service

router = APIRouter()


def _run_sync_in_background(user_id: str, has_history_id: bool):
    """Run sync in background thread so HTTP request doesn't time out."""
    try:
        if has_history_id:
            sync_service.incremental_sync(user_id)
        else:
            sync_service.initial_sync(user_id)
    except Exception as e:
        import traceback
        print(f"BACKGROUND SYNC CRASHED FOR USER {user_id}: {str(e)}")
        traceback.print_exc()


@router.post("/{user_id}")
def sync_emails(user_id: str) -> SyncResponse:
    """Trigger email sync for a user in background."""
    try:
        user_result = supabase.table("users").select("id, gmail_history_id").eq("id", user_id).execute()

        if not user_result.data or len(user_result.data) == 0:
            raise HTTPException(status_code=404, detail="User not found")

        user = user_result.data[0]
        has_history_id = bool(user.get("gmail_history_id"))

        thread = threading.Thread(
            target=_run_sync_in_background,
            args=(user_id, has_history_id),
            daemon=True,
        )
        thread.start()

        return SyncResponse(
            emails_synced=0,
            threads_synced=0,
            status="syncing_in_background",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/status/{user_id}")
def sync_status(user_id: str):
    """Check sync status by counting emails in database."""
    try:
        emails_result = supabase.table("emails").select(
            "id", count="exact"
        ).eq("user_id", user_id).execute()

        chunks_result = supabase.table("email_chunks").select(
            "id", count="exact"
        ).eq("user_id", user_id).execute()

        threads_result = supabase.table("threads").select(
            "id", count="exact"
        ).eq("user_id", user_id).execute()

        return {
            "emails_count": emails_result.count or 0,
            "chunks_count": chunks_result.count or 0,
            "threads_count": threads_result.count or 0,
            "status": "ready" if (emails_result.count or 0) > 0 else "empty",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))