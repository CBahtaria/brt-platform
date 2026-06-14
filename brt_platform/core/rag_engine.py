import asyncio
import hashlib
import logging
from typing import Any

from pydantic import BaseModel

from brt_platform.config import settings
from brt_platform.core.connection_pool import ConnectionPool
from brt_platform.core.embedder import Embedder
from brt_platform.core.hookable import Hookable
from brt_platform.core.reranker import LightweightReranker

logger = logging.getLogger(__name__)

# Graceful degradation: ClickHouse is Project B. Never hard-depend from Phase 0.
try:
    from brt_platform.analytics.clickhouse import ClickHouseClient  # noqa: F401
    CLICKHOUSE_AVAILABLE = True
except ImportError:
    CLICKHOUSE_AVAILABLE = False
    logger.info("ClickHouse unavailable — RAG evaluation will not be stored (Project B).")


class RequestContext(BaseModel):
    tenant_id: str
    user_id: str | None = None
    session_id: str | None = None


class RagResult(BaseModel):
    chunks: list[dict[str, Any]]
    metadata: dict[str, Any]


class BRTRagEngine:
    def __init__(self):
        self.embedder = Embedder()
        self.reranker = LightweightReranker()

    async def query(self, query: str, context: RequestContext, top_k: int = 10) -> RagResult:
        return await Hookable.execute(
            core_func=self._query_impl,
            context=context,
            query=query,
            top_k=top_k,
        )

    async def _query_impl(self, query: str, context: RequestContext, top_k: int = 10) -> RagResult:
        results = await self._hybrid_search(query, context.tenant_id)
        fused = self._rrf(results)
        texts = [r.get("text", "") for r in fused]
        ranked = await self.reranker.rerank(query, texts[:top_k * 2])
        final = [{"text": t, "score": s} for t, s in ranked[:top_k]]

        if CLICKHOUSE_AVAILABLE:
            asyncio.create_task(self._evaluate_and_store(query, final, context.tenant_id))

        return RagResult(
            chunks=final,
            metadata={
                "model": settings.EMBEDDING_MODEL,
                "reranker": settings.RERANKER_MODEL,
                "retrieved": len(fused),
                "returned": len(final),
            },
        )

    async def _hybrid_search(self, query: str, tenant_id: str) -> list[dict]:
        from qdrant_client.models import SearchRequest, SparseVector
        collection_name = f"brt_{tenant_id}"
        client = await ConnectionPool.get_qdrant_client()

        dense_vecs, sparse_vecs = await asyncio.gather(
            self.embedder.embed_dense([query]),
            self.embedder.embed_sparse([query]),
        )

        try:
            results = await client.search_batch(
                collection_name=collection_name,
                requests=[
                    SearchRequest(vector=dense_vecs[0], limit=20, with_payload=True),
                    SearchRequest(
                        sparse_vector=SparseVector(
                            indices=sparse_vecs[0]["indices"],
                            values=sparse_vecs[0]["values"],
                        ),
                        limit=20,
                        with_payload=True,
                    ),
                ],
            )
            seen, combined = set(), []
            for result_list in results:
                for point in result_list:
                    if point.id not in seen:
                        combined.append({"id": point.id, "score": point.score, "text": (point.payload or {}).get("text", "")})
                        seen.add(point.id)
            return combined
        except Exception as e:
            logger.warning(f"Hybrid search failed for '{collection_name}': {e}")
            return []

    def _rrf(self, results: list[dict], k: int = 60) -> list[dict]:
        return sorted(results, key=lambda x: x.get("score", 0), reverse=True)

    async def _evaluate_and_store(self, query: str, chunks: list, tenant_id: str):
        q_hash = hashlib.md5(query.encode()).hexdigest()
        logger.info(f"RAG eval (Phase 3 placeholder): tenant={tenant_id} hash={q_hash} chunks={len(chunks)}")
