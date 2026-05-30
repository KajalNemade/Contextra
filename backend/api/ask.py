from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from storage.database import get_db
from models.db import Repo, RepoStatus
from embeddings.engine import embed_text, search_chunks
from services.llm_provider import answer_question

router = APIRouter(prefix="/ask", tags=["qa"])


class AskRequest(BaseModel):
    repo_id: int
    question: str
    top_k: int = 5


class AskResponse(BaseModel):
    answer: str
    provider: str
    sources: list[str]
    confidence: str
    chunks_used: int


@router.post("", response_model=AskResponse)
async def ask_question(
    request: AskRequest,
    session: AsyncSession = Depends(get_db),
):
    """
    Semantic Q&A about repository code.
    """

    repo = await session.get(
        Repo,
        request.repo_id,
    )

    if not repo:
        raise HTTPException(
            status_code=404,
            detail="Repo not found",
        )

    if repo.status != RepoStatus.READY:
        raise HTTPException(
            status_code=409,
            detail=f"Repo not ready (status: {repo.status}). Wait for indexing.",
        )

    # Embed question
    query_vector = await embed_text(request.question)

    if query_vector is None:
        raise HTTPException(
            status_code=503,
            detail="Embedding service unavailable",
        )

    # Search relevant chunks
    chunks = await search_chunks(
        query_vector=query_vector,
        repo_id=request.repo_id,
        top_k=min(request.top_k, 10),
    )

    # Ask LLM
    try:
        result = await answer_question(
            request.question,
            chunks,
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate answer",
        )

    return AskResponse(
        answer=result["answer"],
        provider=result["provider"],
        sources=result["sources"],
        confidence=result["confidence"],
        chunks_used=len(chunks),
    )