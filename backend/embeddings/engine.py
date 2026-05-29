"""
Embedding engine.
Primary: Ollama (nomic-embed-text) — free, local, zero cost.
Never uses Gemini for embeddings.
"""

from __future__ import annotations
from typing import List, Optional
import httpx
import structlog

from config.settings import settings

log = structlog.get_logger()

COLLECTION_NAME = f"dcrs_chunks_{settings.embedding_version}"


async def embed_text(text: str) -> Optional[List[float]]:
    """Get embedding vector from Ollama."""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.ollama_url}/api/embed",
                json={
                    "model": settings.embedding_model,
                    "input": text,
                },
            )

            response.raise_for_status()

            data = response.json()

            embeddings = data.get("embeddings")

            if embeddings and len(embeddings) > 0:
                return embeddings[0]

            return None

    except Exception as e:
        log.error("Embedding failed", error=str(e))
        return None


async def embed_batch(texts: List[str]) -> List[Optional[List[float]]]:
    """Embed multiple texts."""

    results = []

    for text in texts:
        vec = await embed_text(text)
        results.append(vec)

    return results


async def ensure_collection():
    """Create Qdrant collection if it doesn't exist."""

    try:
        from qdrant_client import AsyncQdrantClient
        from qdrant_client.models import Distance, VectorParams

        client = AsyncQdrantClient(url=settings.qdrant_url)

        collections = await client.get_collections()
        names = [c.name for c in collections.collections]

        if COLLECTION_NAME not in names:
            await client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=settings.embedding_dimension,
                    distance=Distance.COSINE,
                ),
            )

            log.info(
                "Created Qdrant collection",
                name=COLLECTION_NAME,
            )

        await client.close()

    except Exception as e:
        log.error(
            "Could not ensure Qdrant collection",
            error=str(e),
        )


async def upsert_chunk(
    chunk_id: str,
    vector: List[float],
    payload: dict,
):
    """Store embedding chunk in Qdrant."""

    try:
        from qdrant_client import AsyncQdrantClient
        from qdrant_client.models import PointStruct

        client = AsyncQdrantClient(url=settings.qdrant_url)

        await client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=abs(hash(chunk_id)) % (2**63),
                    vector=vector,
                    payload=payload,
                )
            ],
        )

        await client.close()

    except Exception as e:
        log.error(
            "Qdrant upsert failed",
            chunk_id=chunk_id,
            error=str(e),
        )


async def search_chunks(
    query_vector: List[float],
    repo_id: int,
    top_k: int = 5,
    query: str = "",
) -> List[dict]:
    """
    Semantic vector search with reranking.
    """

    try:
        from qdrant_client import AsyncQdrantClient
        from qdrant_client.models import (
            Filter,
            FieldCondition,
            MatchValue,
        )

        client = AsyncQdrantClient(url=settings.qdrant_url)

        results = await client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="repo_id",
                        match=MatchValue(value=repo_id),
                    )
                ]
            ),
            limit=top_k * 3,
        )

        await client.close()

        query_lower = query.lower() if query else ""

        filtered = []

        for r in results:

            payload = r.payload or {}

            path = payload.get(
                "file_path",
                "",
            ).lower()

            function_name = payload.get(
                "function_name",
                "",
            ).lower()

            class_name = payload.get(
                "class_name",
                "",
            )

            score = float(r.score)

            # Skip tests
            if (
                "test" in path
                or "/tests/" in path
                or "\\tests\\" in path
            ):
                continue

            # Boost filename matches
            if query_lower in path:
                score += 0.25

            # Boost function matches
            if query_lower == function_name:
                score += 0.35

            # Boost class matches
            if class_name and query_lower == class_name.lower():
                score += 0.35

            filtered.append(
                {
                    "score": score,
                    **payload,
                }
            )

        # Sort by reranked score
        filtered.sort(
            key=lambda x: x["score"],
            reverse=True,
        )

        return filtered[:top_k]

    except Exception as e:
        log.error(
            "Qdrant search failed",
            error=str(e),
        )
        return []


async def delete_repo_chunks(repo_id: int):
    """Delete all vectors for a repository."""

    try:
        from qdrant_client import AsyncQdrantClient
        from qdrant_client.models import (
            Filter,
            FieldCondition,
            MatchValue,
        )

        client = AsyncQdrantClient(url=settings.qdrant_url)

        await client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="repo_id",
                        match=MatchValue(value=repo_id),
                    )
                ]
            ),
        )

        await client.close()

    except Exception as e:
        log.error(
            "Qdrant delete failed",
            repo_id=repo_id,
            error=str(e),
        )