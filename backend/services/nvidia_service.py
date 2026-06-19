import os
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv()


def rerank_chunks(query: str, chunks: list[dict], top_k: int = 5) -> list[dict]:
    """
    Rerank retrieved chunks by relevance using NVIDIA NIM LLM scoring.
    Falls back to returning first top_k chunks if NVIDIA API fails.
    """
    try:
        api_key = os.getenv("NVIDIA_API_KEY")
        base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

        if not api_key or not chunks:
            return chunks[:top_k]

        scored_chunks = []

        for chunk in chunks:
            try:
                chunk_text = chunk.get("chunk_text", chunk.get("content", ""))[:500]

                prompt = (
                    "Rate the relevance of this email excerpt to the query on a scale of 0-10.\n"
                    "Reply with ONLY a number.\n\n"
                    f"Query: {query}\n"
                    f"Email excerpt: {chunk_text}\n\n"
                    "Relevance score (0-10):"
                )

                with httpx.Client(timeout=10.0) as client:
                    response = client.post(
                        f"{base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": "nvidia/llama-3.1-nemotron-nano-8b-instruct",
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": 10,
                            "temperature": 0.1,
                        },
                    )
                    response.raise_for_status()

                result = response.json()
                score_text = (
                    result.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "0")
                    .strip()
                )

                # Parse score - extract first number found
                import re
                score_match = re.search(r"(\d+\.?\d*)", score_text)
                score = float(score_match.group(1)) if score_match else 0.0
                score = min(score, 10.0)

                scored_chunks.append({"chunk": chunk, "score": score})
            except Exception:
                scored_chunks.append({"chunk": chunk, "score": 0.0})

        # Sort by score descending
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)

        return [item["chunk"] for item in scored_chunks[:top_k]]

    except Exception:
        # Fallback: return first top_k chunks without reranking
        return chunks[:top_k]
