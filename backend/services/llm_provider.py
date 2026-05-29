"""
LLM provider abstraction.
Uses:
- Ollama locally
- Gemini fallback
"""

from __future__ import annotations

from typing import Optional, List

import httpx
import structlog

from config.settings import settings

log = structlog.get_logger()


# =========================
# OLLAMA
# =========================
async def _ask_ollama(prompt: str) -> Optional[str]:
    """Ask Ollama local model."""

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{settings.ollama_url}/api/generate",
                json={
                    "model": settings.llm_model,
                    "prompt": prompt,
                    "stream": False,
                },
            )

            response.raise_for_status()

            data = response.json()

            result = data.get("response", "").strip()

            if not result:
                log.warning("Ollama returned empty response")
                return None

            return result

    except Exception as e:
        import traceback

        traceback.print_exc()

        log.warning(
            "Ollama unavailable",
            error=repr(e),
            error_type=type(e).__name__,
        )

        return None

# =========================
# GEMINI FALLBACK
# =========================
async def _ask_gemini(prompt: str) -> Optional[str]:
    """Fallback Gemini provider."""

    if not settings.gemini_api_key:
        return None

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)

        model = genai.GenerativeModel("gemini-1.5-flash")

        response = model.generate_content(prompt)

        text = response.text.strip()

        if not text:
            return None

        return text

    except Exception as e:
        log.warning("Gemini unavailable", error=str(e))
        return None


# =========================
# PROMPT BUILDER
# =========================
def _build_prompt(question: str, chunks: List[dict]) -> str:
    """
    Build compact repository context prompt.
    """

    context_parts = []

    for i, chunk in enumerate(chunks, start=1):
        path = chunk.get("file_path", "unknown")
        body = chunk.get("body", "")
        fn_name = chunk.get("function_name", "unknown")

        # Keep prompt smaller
        body = body[:500]

        context_parts.append(
            f"""
FILE: {path}
FUNCTION: {fn_name}

CODE:
{body}
"""
        )

    context = "\n\n".join(context_parts)

    return f"""
You are a senior software engineer.

Answer the question ONLY using the provided repository context.

If the answer is unclear, say:
"I could not find this in the indexed repository."

QUESTION:
{question}

REPOSITORY CONTEXT:
{context}

Give a concise technical explanation.
""".strip()


# =========================
# MAIN QA ENTRY
# =========================
async def answer_question(
    question: str,
    chunks: List[dict],
) -> dict:
    """
    Answer repository question using semantic chunks.
    """

    if not chunks:
        return {
            "answer": "No relevant code found.",
            "provider": "none",
            "sources": [],
            "confidence": "low",
        }

    sources = list(
        {
            c.get("file_path")
            for c in chunks
            if c.get("file_path")
        }
    )

    prompt = _build_prompt(question, chunks)

    # -------------------------
    # Try Ollama first
    # -------------------------
    answer = await _ask_ollama(prompt)

    if answer:
        return {
            "answer": answer,
            "provider": "ollama",
            "sources": sources,
            "confidence": "high",
        }

    # -------------------------
    # Gemini fallback
    # -------------------------
    answer = await _ask_gemini(prompt)

    if answer:
        return {
            "answer": answer,
            "provider": "gemini",
            "sources": sources,
            "confidence": "medium",
        }

    # -------------------------
    # Final fallback
    # -------------------------
    return {
        "answer": "AI providers unavailable, but semantic search succeeded.",
        "provider": "search_only",
        "sources": sources,
        "confidence": "low",
    }


# =========================
# CODE SUMMARY
# =========================
async def summarize_code(
    code: str,
    context_hint: str = "",
) -> Optional[str]:
    """
    Generate short code summary.
    """

    prompt = f"""
Summarize this code in 2-3 concise sentences.

{f"Context: {context_hint}" if context_hint else ""}

CODE:
{code[:2000]}

SUMMARY:
""".strip()

    result = await _ask_ollama(prompt)

    if result:
        return result

    return await _ask_gemini(prompt)