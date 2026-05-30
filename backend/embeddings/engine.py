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
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.ollama_url}/api/embeddings",
                json={"model": settings.embedding_model, "prompt": text},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("embedding")
    except Exception as e:
        log.error("Embedding failed", error=str(e))
        return None


async def embed_batch(texts: List[str]) -> List[Optional[List[float]]]:
    """Embed a list of texts. Returns same-length list (None if failed)."""
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
            log.info("Created Qdrant collection", name=COLLECTION_NAME)
        await client.close()
    except Exception as e:
        log.error("Could not ensure Qdrant collection", error=str(e))


async def upsert_chunk(chunk_id: str, vector: List[float], payload: dict):
    """Upsert a single chunk into Qdrant."""
    try:
        from qdrant_client import AsyncQdrantClient
        from qdrant_client.models import PointStruct

        client = AsyncQdrantClient(url=settings.qdrant_url)
        await client.upsert(
            collection_name=COLLECTION_NAME,
            points=[PointStruct(id=abs(hash(chunk_id)) % (2**63), vector=vector, payload=payload)],
        )
        await client.close()
    except Exception as e:
        log.error("Qdrant upsert failed", chunk_id=chunk_id, error=str(e))


async def search_chunks(query_vector: List[float], repo_id: int, top_k: int = 5) -> List[dict]:
    """Semantic search with repo filter."""
    try:
        from qdrant_client import AsyncQdrantClient
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        client = AsyncQdrantClient(url=settings.qdrant_url)
        results = await client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=Filter(
                must=[FieldCondition(key="repo_id", match=MatchValue(value=repo_id))]
            ),
            limit=top_k,
        )
        await client.close()
        return [{"score": r.score, **r.payload} for r in results]
    except Exception as e:
        log.error("Qdrant search failed", error=str(e))
        return []


async def delete_repo_chunks(repo_id: int):
    """Remove all vectors for a repo (on reindex)."""
    try:
        from qdrant_client import AsyncQdrantClient
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        client = AsyncQdrantClient(url=settings.qdrant_url)
        await client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[FieldCondition(key="repo_id", match=MatchValue(value=repo_id))]
            ),
        )
        await client.close()
    except Exception as e:
        log.error("Qdrant delete failed", repo_id=repo_id, error=str(e))
