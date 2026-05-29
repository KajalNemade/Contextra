from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from storage.database import get_db
from models.db import Repo, Function, RepoStatus
from embeddings.engine import embed_text, search_chunks

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/{repo_id}")
async def search(
    repo_id: int,
    q: str = Query(..., min_length=1),
    top_k: int = Query(default=10, le=20),
    session: AsyncSession = Depends(get_db),
):
    """
    Semantic repository search.
    """

    repo = await session.get(
        Repo,
        repo_id,
    )

    if not repo:
        raise HTTPException(
            404,
            "Repo not found",
        )

    if repo.status != RepoStatus.READY:
        raise HTTPException(
            409,
            f"Repo not ready (status: {repo.status})",
        )

    # Embed query
    query_vector = await embed_text(q)

    # Fallback keyword search
    if not query_vector:

        result = await session.execute(
            select(Function)
            .where(Function.repo_id == repo_id)
            .where(Function.name.ilike(f"%{q}%"))
            .limit(top_k)
        )

        fns = result.scalars().all()

        return {
            "query": q,
            "results": [
                {
                    "file_path": None,
                    "function_name": fn.name,
                    "score": 1.0,
                    "body": fn.body[:300] if fn.body else "",
                }
                for fn in fns
            ],
            "search_type": "keyword_fallback",
        }

    # Semantic vector search
    chunks = await search_chunks(
    query_vector=query_vector,
    repo_id=repo_id,
    top_k=top_k,
    query=q,
)

    return {
        "query": q,
        "results": chunks,
        "search_type": "semantic",
    }