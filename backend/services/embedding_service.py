import logging
import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

from db.supabase_client import get_supabase

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

logger = logging.getLogger(__name__)

# text-embedding-004 is unavailable on many keys; gemini-embedding-001 supports
# outputDimensionality=768 to match our pgvector schema.
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768
EMBED_API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{EMBEDDING_MODEL}:embedContent"
)


def _get_api_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing in backend/.env")
    return api_key


def embed_text(text: str) -> list[float]:
    """Generate a 768-dimensional embedding vector for the given text."""
    if not text or not text.strip():
        raise ValueError("Cannot embed empty text")

    response = httpx.post(
        EMBED_API_URL,
        params={"key": _get_api_key()},
        json={
            "content": {"parts": [{"text": text[:8000]}]},
            "outputDimensionality": EMBEDDING_DIMENSIONS,
        },
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    embedding = payload.get("embedding", {}).get("values")
    if not embedding:
        raise RuntimeError(f"Unexpected embedding response: {payload}")
    return embedding


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks of approximately chunk_size tokens."""
    if not text or not text.strip():
        return []

    try:
        import tiktoken

        encoder = tiktoken.get_encoding("cl100k_base")
        tokens = encoder.encode(text)
        if not tokens:
            return []

        chunks: list[str] = []
        start = 0
        while start < len(tokens):
            end = min(start + chunk_size, len(tokens))
            chunk = encoder.decode(tokens[start:end]).strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(tokens):
                break
            start = max(end - overlap, start + 1)
        return chunks
    except Exception as exc:
        logger.warning("tiktoken unavailable, falling back to word-based chunking: %s", exc)
        words = text.split()
        if not words:
            return []
        # Rough fallback: ~1.3 words per token
        word_chunk_size = max(int(chunk_size * 1.3), 1)
        word_overlap = max(int(overlap * 1.3), 0)
        chunks = []
        start = 0
        while start < len(words):
            end = start + word_chunk_size
            chunk = " ".join(words[start:end]).strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(words):
                break
            start = max(end - word_overlap, start + 1)
        return chunks


def _build_metadata(metadata: dict) -> dict[str, Any]:
    return {
        "sender": metadata.get("sender", ""),
        "sender_email": metadata.get("sender_email", ""),
        "subject": metadata.get("subject", ""),
        "received_at": metadata.get("received_at", ""),
        "gmail_message_id": metadata.get("gmail_message_id", ""),
        "gmail_thread_id": metadata.get("gmail_thread_id", ""),
    }


def store_email_embeddings(
    email_id: str,
    user_id: str,
    body_text: str,
    metadata: dict,
) -> int:
    """Chunk email text, generate embeddings, and store in Supabase email_chunks table."""
    if not body_text or not body_text.strip():
        return 0

    chunks = chunk_text(body_text)
    if not chunks:
        return 0

    supabase = get_supabase()
    supabase.table("email_chunks").delete().eq("email_id", email_id).execute()

    chunk_metadata = _build_metadata(metadata)
    stored = 0
    errors: list[str] = []

    for chunk_index, chunk in enumerate(chunks):
        try:
            embedding = embed_text(chunk)
            supabase.table("email_chunks").insert(
                {
                    "email_id": email_id,
                    "user_id": user_id,
                    "chunk_text": chunk,
                    "chunk_index": chunk_index,
                    "embedding": embedding,
                    "metadata": chunk_metadata,
                }
            ).execute()
            stored += 1
        except Exception as exc:
            message = f"chunk {chunk_index} for email {email_id}: {exc}"
            logger.error(message)
            errors.append(message)

    if stored == 0 and errors:
        raise RuntimeError("; ".join(errors))

    return stored


def reembed_user_emails(user_id: str) -> dict[str, int | str]:
    """Re-chunk and re-embed all emails already stored for a user."""
    supabase = get_supabase()
    user_result = supabase.table("users").select("id").eq("id", user_id).execute()
    if not user_result.data:
        raise ValueError(f"User {user_id} not found")

    emails_result = (
        supabase.table("emails")
        .select(
            "id, user_id, body_text, snippet, sender, sender_email, subject, "
            "received_at, gmail_message_id, gmail_thread_id"
        )
        .eq("user_id", user_id)
        .execute()
    )

    emails = emails_result.data or []
    emails_processed = 0
    chunks_created = 0
    skipped = 0
    errors: list[str] = []

    for email in emails:
        body_text = (email.get("body_text") or email.get("snippet") or "").strip()
        if not body_text:
            skipped += 1
            continue

        try:
            created = store_email_embeddings(
                email_id=email["id"],
                user_id=user_id,
                body_text=body_text,
                metadata={
                    "sender": email.get("sender", ""),
                    "sender_email": email.get("sender_email", ""),
                    "subject": email.get("subject", ""),
                    "received_at": email.get("received_at", ""),
                    "gmail_message_id": email.get("gmail_message_id", ""),
                    "gmail_thread_id": email.get("gmail_thread_id", ""),
                },
            )
            if created:
                emails_processed += 1
                chunks_created += created
            else:
                skipped += 1
        except Exception as exc:
            errors.append(f"{email.get('gmail_message_id', email['id'])}: {exc}")

    status = "completed" if not errors else "completed_with_errors"
    return {
        "emails_processed": emails_processed,
        "chunks_created": chunks_created,
        "emails_skipped": skipped,
        "errors": len(errors),
        "status": status,
    }


def search_similar_chunks(query: str, user_id: str, top_k: int = 20) -> list[dict]:
    """Search for email chunks semantically similar to the query using vector similarity."""
    embedding = embed_text(query)
    supabase = get_supabase()

    result = supabase.rpc(
        "search_email_chunks",
        {
            "query_embedding": embedding,
            "target_user_id": user_id,
            "match_count": top_k,
        },
    ).execute()

    return result.data if result.data else []
