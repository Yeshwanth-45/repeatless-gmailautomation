from fastapi import APIRouter, HTTPException, Query

from db.supabase_client import supabase
from models.schemas import (
    ChatMessageRecord,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionResponse,
)
from services import embedding_service, gemini_service, nvidia_service

router = APIRouter()


@router.post("/session")
def create_chat_session(body: ChatSessionCreate) -> ChatSessionResponse:
    """Create a new chat session for a user."""
    try:
        result = supabase.table("chat_sessions").insert({
            "user_id": body.user_id,
            "title": "New Chat",
        }).execute()

        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=500, detail="Failed to create chat session")

        session = result.data[0]
        return ChatSessionResponse(
            id=session["id"],
            user_id=session["user_id"],
            title=session.get("title", "New Chat"),
            created_at=str(session.get("created_at", "")),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create chat session: {str(e)}")


@router.post("/message")
def send_chat_message(body: ChatMessageRequest) -> ChatMessageResponse:
    """Process a chat message through the RAG pipeline."""
    try:
        # Step 1: Search similar email chunks
        chunks = embedding_service.search_similar_chunks(
            query=body.message,
            user_id=body.user_id,
            top_k=20,
        )

        # Step 2: Rerank chunks using NVIDIA NIM
        reranked_chunks = nvidia_service.rerank_chunks(
            query=body.message,
            chunks=chunks,
            top_k=5,
        )

        # Step 3: Get conversation history (last 6 messages)
        history_result = supabase.table("chat_messages").select("*").eq(
            "session_id", body.session_id
        ).order("created_at", desc=True).limit(6).execute()

        conversation_history = []
        if history_result.data:
            # Reverse to get chronological order
            for msg in reversed(history_result.data):
                conversation_history.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                })

        # Step 4: Generate response with Gemini
        response = gemini_service.chat_with_emails(
            question=body.message,
            retrieved_chunks=reranked_chunks,
            conversation_history=conversation_history,
        )

        answer = response.get("answer", "")
        sources = response.get("sources", [])

        # Step 5: Store user message in chat_messages
        supabase.table("chat_messages").insert({
            "session_id": body.session_id,
            "role": "user",
            "content": body.message,
            "sources": None,
        }).execute()

        # Step 6: Store assistant response in chat_messages
        supabase.table("chat_messages").insert({
            "session_id": body.session_id,
            "role": "assistant",
            "content": answer,
            "sources": sources,
        }).execute()

        # Update session title based on first message
        if not conversation_history:
            title = body.message[:50] + ("..." if len(body.message) > 50 else "")
            supabase.table("chat_sessions").update({
                "title": title,
            }).eq("id", body.session_id).execute()

        return ChatMessageResponse(content=answer, sources=sources)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")


@router.get("/sessions")
def list_chat_sessions(
    user_id: str = Query(..., description="User ID"),
) -> list[ChatSessionResponse]:
    """List all chat sessions for a user ordered by most recent first."""
    try:
        result = supabase.table("chat_sessions").select("*").eq(
            "user_id", user_id
        ).order("created_at", desc=True).execute()

        sessions = []
        for s in (result.data or []):
            sessions.append(ChatSessionResponse(
                id=s["id"],
                user_id=s["user_id"],
                title=s.get("title", "New Chat"),
                created_at=str(s.get("created_at", "")),
            ))

        return sessions
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")


@router.get("/sessions/{session_id}/messages")
def get_session_messages(session_id: str) -> list[ChatMessageRecord]:
    """Get all messages in a chat session ordered chronologically."""
    try:
        result = supabase.table("chat_messages").select("*").eq(
            "session_id", session_id
        ).order("created_at", desc=False).execute()

        messages = []
        for m in (result.data or []):
            messages.append(ChatMessageRecord(
                id=m["id"],
                session_id=m["session_id"],
                role=m.get("role", "user"),
                content=m.get("content", ""),
                sources=m.get("sources"),
                created_at=str(m.get("created_at", "")),
            ))

        return messages
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")
