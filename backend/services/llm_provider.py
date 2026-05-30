"""
LLM provider abstraction.
Decision logic:
  Question → retrieve context → Ollama? YES → answer
                                           NO → Gemini? YES → answer
                                                         NO → return search results only
Never fails. Degrades gracefully.
Never used for parsing/search/embeddings.
"""
from __future__ import annotations
from typing import Optional, List
import httpx
import structlog
from config.settings import settings
log = structlog.get_logger()


async def _ask_ollama(prompt: str) -> Optional[str]:
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{settings.ollama_url}/api/generate",
                json={
                    "model": settings.llm_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": 800},
                },
            )

            response.raise_for_status()

            data = response.json()

            return data.get("response", "").strip()

    except Exception as e:
        log.warning(
            "Ollama unavailable",
            error=repr(e),
        )
        return None


async def _ask_gemini(prompt: str) -> Optional[str]:
    if not settings.gemini_api_key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        log.warning("Gemini unavailable", error=str(e))
        return None


def _build_prompt(question: str, chunks: List[dict]) -> str:
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        path = chunk.get("file_path", "unknown")
        body = chunk.get("body", "")[:700]
        fn_name = chunk.get("function_name", "")
        context_parts.append(f"[{i}] {path} — {fn_name}\n```\n{body}\n```")

    context = "\n\n".join(context_parts)

    return f"""You are a code intelligence assistant. Answer based ONLY on the code context provided below.
Always cite which files your answer comes from.
If you cannot answer from the context, say so — do not hallucinate.

Context from repository:
{context}

Question: {question}

Answer (cite sources):"""


async def answer_question(
    question: str, chunks: List[dict]
) -> dict:
    """
    Returns: {
        "answer": str,
        "provider": str,   # "ollama" | "gemini" | "search_only"
        "sources": [str],
        "confidence": str  # "high" | "medium" | "low"
    }
    """
    sources = list({c.get("file_path", "") for c in chunks if c.get("file_path")})

    if not chunks:
        return {
            "answer": "No relevant code found for this question.",
            "provider": "none",
            "sources": [],
            "confidence": "low",
        }

    prompt = _build_prompt(question, chunks)

    # Try Ollama first
    answer = await _ask_ollama(prompt)
    if answer:
        return {
            "answer": answer,
            "provider": "ollama",
            "sources": sources,
            "confidence": "high" if len(chunks) >= 3 else "medium",
        }

    # Fallback: Gemini
    answer = await _ask_gemini(prompt)
    if answer:
        return {
            "answer": answer,
            "provider": "gemini",
            "sources": sources,
            "confidence": "medium",
        }

    # Final fallback: return search results as structured text
    search_text = "AI unavailable. Relevant code locations:\n"
    for chunk in chunks:
        search_text += f"- {chunk.get('file_path')} ({chunk.get('function_name', '')})\n"

    return {
        "answer": search_text,
        "provider": "search_only",
        "sources": sources,
        "confidence": "low",
    }


async def summarize_code(code: str, context_hint: str = "") -> Optional[str]:
    """Generate a short natural-language summary of a code chunk."""
    prompt = f"""Summarize what this code does in 2-3 sentences. Be specific. No preamble.
{f'Context: {context_hint}' if context_hint else ''}

Code:
```
{code[:2000]}
```

Summary:"""

    result = await _ask_ollama(prompt)
    if result:
        return result
    return await _ask_gemini(prompt)