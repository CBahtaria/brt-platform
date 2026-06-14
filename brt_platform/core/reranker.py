import asyncio
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple

from brt_platform.config import settings

logger = logging.getLogger(__name__)

_pool = ThreadPoolExecutor(max_workers=1)


class SharedModelPool:
    _model = None
    _lock = threading.Lock()

    @classmethod
    def get_model(cls):
        if cls._model is None:
            with cls._lock:
                if cls._model is None:
                    from sentence_transformers import CrossEncoder
                    logger.info(f"Loading reranker: {settings.RERANKER_MODEL}")
                    cls._model = CrossEncoder(settings.RERANKER_MODEL)
                    logger.info("Reranker ready.")
        return cls._model


class LightweightReranker:
    async def rerank(self, query: str, chunks: List[str]) -> List[Tuple[str, float]]:
        if not chunks:
            return []
        model = SharedModelPool.get_model()
        loop = asyncio.get_event_loop()
        pairs = [(query, chunk) for chunk in chunks]
        scores = await loop.run_in_executor(
            _pool,
            lambda: model.predict(pairs, show_progress_bar=False).tolist()
        )
        return sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)
