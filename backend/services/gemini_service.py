import json
import os
import re
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
NVIDIA_MODEL = "meta/llama-3.1-8b-instruct"


def _nvidia_generate(prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
    """Call NVIDIA NIM to generate text. Returns empty string on failure."""
    if not NVIDIA_API_KEY:
        return ""
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{NVIDIA_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {NVIDIA_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": NVIDIA_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": 0.9,
                    "stream": False,
                },
            )
            response.raise_for_status()
            return (
                response.json()
                .get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )
    except Exception:
        return ""


def _try_gemini(prompt: str) -> Optional[str]:
    """Try Gemini models in order of quota availability. Returns None if all fail."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return None
    # Try models from highest free-tier quota to lowest
    models_to_try = [
        "gemini-2.0-flash-lite",   # 1500 req/day free
        "gemini-1.5-flash-8b",     # 1500 req/day free
        "gemini-1.5-flash",         # 1500 req/day free
        "gemini-2.0-flash",         # 500 req/day free
    ]
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                err = str(e)
                # Only skip to next model on quota/not-found errors
                if "429" in err or "404" in err or "quota" in err.lower():
                    continue
                raise
    except Exception:
        pass
    return None


def _generate(prompt: str, max_tokens: int = 512) -> str:
    """Try Gemini first, fall back to NVIDIA NIM."""
    result = _try_gemini(prompt)
    if result:
        return result
    result = _nvidia_generate(prompt, max_tokens=max_tokens)
    if result:
        return result
    return ""


def summarize_email(subject: str, sender: str, body_text: str) -> str:
    """Summarize a single email in 2-3 sentences."""
    try:
        prompt = (
            "Summarize this email in 2-3 sentences. Be concise and capture "
            "the key point and any action required.\n\n"
            f"From: {sender}\n"
            f"Subject: {subject}\n"
            f"Body: {body_text[:3000]}\n\n"
            "Summary:"
        )
        result = _generate(prompt, max_tokens=200)
        return result
    except Exception:
        return ""


def summarize_thread(messages: list[dict]) -> str:
    """Summarize an entire email thread."""
    try:
        formatted_messages = ""
        for i, msg in enumerate(messages, 1):
            sender = msg.get("sender", "Unknown")
            body = msg.get("body_text", msg.get("snippet", ""))[:1000]
            formatted_messages += f"\nMessage {i} (from {sender}):\n{body}\n"

        prompt = (
            f"Below is an email thread with {len(messages)} messages. "
            "Write a 3-4 sentence summary that captures:\n"
            "- What the thread is about\n"
            "- Key decisions or information exchanged\n"
            "- Current status or next steps\n\n"
            f"Thread:\n{formatted_messages}\n\n"
            "Thread Summary:"
        )
        return _generate(prompt, max_tokens=300)
    except Exception:
        return ""


def categorize_email(subject: str, sender: str, snippet: str) -> str:
    """Classify an email into one of the predefined categories."""
    try:
        prompt = (
            "Classify this email into EXACTLY ONE of these categories:\n"
            "Newsletter, Job/Recruitment, Finance, Notifications, Personal, Work/Professional\n\n"
            f"From: {sender}\n"
            f"Subject: {subject}\n"
            f"Preview: {snippet}\n\n"
            "Reply with ONLY the category name, nothing else."
        )
        result = _generate(prompt, max_tokens=20)
        return result if result else "Work/Professional"
    except Exception:
        return "Work/Professional"


def draft_email(prompt: str, user_name: str = "User") -> dict:
    """Draft a professional email and return {subject, body}."""
    try:
        generation_prompt = (
            "Draft a professional email based on this request:\n"
            f'"{prompt}"\n\n'
            "Return ONLY a JSON object in this exact format:\n"
            '{"subject": "email subject here", "body": "email body here"}'
        )
        response_text = _generate(generation_prompt, max_tokens=600)

        # Handle markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        try:
            result = json.loads(response_text)
            return {
                "subject": result.get("subject", "Draft"),
                "body": result.get("body", response_text),
            }
        except json.JSONDecodeError:
            return {"subject": "Draft", "body": response_text}
    except Exception as e:
        return {"subject": "Draft", "body": f"Error generating draft: {str(e)}"}


def draft_reply(prompt: str, thread_messages: list[dict], user_name: str = "User") -> str:
    """Draft a reply based on the thread context and user's intent."""
    try:
        formatted_thread = ""
        for i, msg in enumerate(thread_messages, 1):
            sender = msg.get("sender", "Unknown")
            body = msg.get("body_text", msg.get("snippet", ""))[:1000]
            formatted_thread += f"\nMessage {i} (from {sender}):\n{body}\n"

        generation_prompt = (
            "You are drafting a reply email. Here is the full thread context:\n"
            f"{formatted_thread}\n\n"
            "The user wants to reply with this intent:\n"
            f'"{prompt}"\n\n'
            "Write ONLY the reply body text. Be professional and contextually appropriate.\n"
            "Do not include subject line or headers."
        )
        return _generate(generation_prompt, max_tokens=500)
    except Exception as e:
        return f"Error generating reply: {str(e)}"


def chat_with_emails(
    question: str,
    retrieved_chunks: list[dict],
    conversation_history: Optional[list[dict]] = None,
) -> dict:
    """Answer a question using retrieved email chunks as context."""
    try:
        system_prompt = (
            "You are an email intelligence assistant with access to the user's emails.\n\n"
            "STRICT RULES — FOLLOW THESE WITHOUT EXCEPTION:\n"
            "1. Answer ONLY using information from the Email Knowledge Base provided below.\n"
            "2. If the answer cannot be found in the provided emails, respond with exactly:\n"
            '   "I couldn\'t find that information in your emails."\n'
            "3. ALWAYS cite your source for every piece of information:\n"
            "   - Mention the sender name, email subject, and date\n"
            "4. If multiple emails discuss the same topic, synthesize them into one\n"
            "   coherent answer and clearly attribute each part to its source.\n"
            "5. Never guess, infer, or use any knowledge outside the provided emails.\n"
            '6. For job rejection queries: look for keywords like "unfortunately",\n'
            '   "not moving forward", "other candidates", "not selected".'
        )

        # Build email knowledge base
        knowledge_base = "\n\nEmail Knowledge Base:\n"
        sources = []
        seen_message_ids = set()

        for chunk in retrieved_chunks:
            metadata = chunk.get("metadata", {})
            sender = metadata.get("sender", "Unknown")
            sender_email = metadata.get("sender_email", "")
            subject = metadata.get("subject", "No subject")
            date = metadata.get("received_at", "Unknown date")
            gmail_message_id = metadata.get("gmail_message_id", "")
            chunk_text = chunk.get("chunk_text", chunk.get("content", ""))

            knowledge_base += (
                f"\n[Source: {sender} | {subject} | {date}]\n{chunk_text}\n---"
            )

            if gmail_message_id and gmail_message_id not in seen_message_ids:
                seen_message_ids.add(gmail_message_id)
                sources.append({
                    "sender": sender,
                    "sender_email": sender_email,
                    "subject": subject,
                    "date": date,
                    "gmail_message_id": gmail_message_id,
                })

        # Build conversation history
        history_text = ""
        if conversation_history:
            recent_history = conversation_history[-6:]
            history_text = "\n\nConversation History:\n"
            for msg in recent_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                history_text += f"{role}: {content}\n"

        full_prompt = (
            f"{system_prompt}\n\n"
            f"{knowledge_base}"
            f"{history_text}\n\n"
            f"Question: {question}"
        )

        answer = _generate(full_prompt, max_tokens=800)

        if not answer:
            answer = "I'm sorry, I couldn't process your question right now. Please try again in a moment."

        return {
            "answer": answer,
            "sources": sources,
        }
    except Exception as e:
        return {
            "answer": f"Sorry, I encountered an error: {str(e)}",
            "sources": [],
        }
