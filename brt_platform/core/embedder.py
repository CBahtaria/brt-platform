import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple

from brt_platform.config import settings
from brt_platform.exceptions import EmbeddingError

logger = logging.getLogger(__name__)

_pool = ThreadPoolExecutor(max_workers=1)


class Embedder:
    _dense_model = None
    _sparse_model = None
    _instance: 'Embedder | None' = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    async def load_models(cls):
        if cls._dense_model and cls._sparse_model:
            return
        logger.info("Loading embedding models (non-blocking)...")
        loop = asyncio.get_event_loop()
        cls._dense_model, cls._sparse_model = await loop.run_in_executor(_pool, cls._load_sync)
        logger.info("Embedding models ready.")

    @classmethod
    def _load_sync(cls) -> Tuple:
        from sentence_transformers import SentenceTransformer
        from fastembed import SparseTextEmbedding
        dense = SentenceTransformer(settings.EMBEDDING_MODEL)
        sparse = SparseTextEmbedding(settings.SPARSE_MODEL)
        return dense, sparse

    async def embed_dense(self, texts: List[str]) -> List[List[float]]:
        if not self._dense_model:
            raise EmbeddingError("Dense model not loaded. Call Embedder.load_models() first.")
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _pool,
            lambda: self._dense_model.encode(texts, batch_size=32, show_progress_bar=False).tolist()
        )

    async def embed_sparse(self, texts: List[str]) -> List[dict]:
        if not self._sparse_model:
            raise EmbeddingError("Sparse model not loaded. Call Embedder.load_models() first.")
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            _pool,
            lambda: list(self._sparse_model.embed(texts, batch_size=32))
        )
        return [{"indices": r.indices.tolist(), "values": r.values.tolist()} for r in results]
