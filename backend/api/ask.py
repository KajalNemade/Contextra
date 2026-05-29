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

    print("=" * 50)
    print("QUESTION:", request.question)

    # Embed question
    query_vector = await embed_text(request.question)

    print("VECTOR EXISTS:", query_vector is not None)

    if query_vector:
        print("VECTOR SIZE:", len(query_vector))

    if query_vector is None:
        raise HTTPException(
            status_code=503,
            detail="Embedding service unavailable",
        )

    # FIXED SEARCH CALL
    chunks = await search_chunks(
    query_vector=query_vector,
    repo_id=request.repo_id,
    top_k=min(request.top_k, 8),
    query=request.question,
    )

    print("CHUNKS FOUND:", len(chunks))

    for c in chunks[:3]:
        print(
            "FOUND:",
            c.get("file_path"),
            c.get("function_name"),
        )

    print("=" * 50)

    # Ask LLM
    try:
        result = await answer_question(
            request.question,
            chunks,
        )

    except Exception as e:
        import traceback

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    return AskResponse(
        answer=result["answer"],
        provider=result["provider"],
        sources=result["sources"],
        confidence=result["confidence"],
        chunks_used=len(chunks),
    )