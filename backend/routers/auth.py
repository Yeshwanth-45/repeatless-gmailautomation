import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow

from db.supabase_client import supabase
from models.schemas import UserResponse

# Always load backend/.env explicitly so uvicorn reload picks up credential changes.
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

router = APIRouter()

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/userinfo.email",
]


def _oauth_settings() -> tuple[str, str, str, str]:
    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "")
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

    if not client_id or client_id == "your_google_oauth_client_id":
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_CLIENT_ID is missing or still set to the placeholder in backend/.env",
        )
    if not client_secret or client_secret == "your_google_oauth_client_secret":
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_CLIENT_SECRET is missing or still set to the placeholder in backend/.env",
        )
    if not redirect_uri:
        raise HTTPException(status_code=500, detail="GOOGLE_REDIRECT_URI is missing in backend/.env")

    return client_id, client_secret, redirect_uri, frontend_url


def _oauth_flow() -> Flow:
    client_id, client_secret, redirect_uri, _ = _oauth_settings()
    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }
    return Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=redirect_uri,
        autogenerate_code_verifier=False,
    )


@router.get("/gmail/login")
def gmail_login():
    """Redirect user to Google OAuth consent screen."""
    try:
        flow = _oauth_flow()
        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        return RedirectResponse(url=authorization_url)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate OAuth: {str(e)}")


@router.get("/gmail/callback")
async def gmail_callback(code: str):
    """Handle OAuth callback, exchange code for tokens, upsert user."""
    try:
        _, _, _, frontend_url = _oauth_settings()
        flow = _oauth_flow()
        flow.fetch_token(code=code)
        credentials = flow.credentials

        access_token = credentials.token
        refresh_token = credentials.refresh_token
        token_expiry = credentials.expiry.isoformat() if credentials.expiry else None

        # Get user email from Google userinfo API
        async with httpx.AsyncClient() as client:
            userinfo_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            userinfo_response.raise_for_status()
            userinfo = userinfo_response.json()

        email = userinfo.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Could not retrieve email from Google")

        # Upsert user in Supabase
        try:
            existing_user = supabase.table("users").select("*").eq("email", email).execute()
        except Exception as db_error:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Google sign-in succeeded, but the database is unreachable. "
                    "Check SUPABASE_URL and SUPABASE_SERVICE_KEY in backend/.env. "
                    f"Original error: {db_error}"
                ),
            ) from db_error

        if existing_user.data and len(existing_user.data) > 0:
            user_id = existing_user.data[0]["id"]
            supabase.table("users").update({
                "gmail_access_token": access_token,
                "gmail_refresh_token": refresh_token,
                "token_expiry": token_expiry,
            }).eq("id", user_id).execute()
        else:
            insert_result = supabase.table("users").insert({
                "email": email,
                "gmail_access_token": access_token,
                "gmail_refresh_token": refresh_token,
                "token_expiry": token_expiry,
            }).execute()
            user_id = insert_result.data[0]["id"] if insert_result.data else None

        if not user_id:
            raise HTTPException(status_code=500, detail="Failed to create or update user")

        return RedirectResponse(url=f"{frontend_url}/dashboard?user_id={user_id}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {str(e)}")


@router.get("/me")
def get_current_user(user_id: str) -> UserResponse:
    """Get user info by user_id."""
    try:
        result = supabase.table("users").select("id, email, created_at").eq("id", user_id).execute()

        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=404, detail="User not found")

        user = result.data[0]
        return UserResponse(
            id=user["id"],
            email=user["email"],
            created_at=str(user.get("created_at", "")),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")