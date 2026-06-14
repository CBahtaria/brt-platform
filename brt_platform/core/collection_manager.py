import asyncio
import logging

from brt_platform.config import settings, RedisKeyPrefix
from brt_platform.core.connection_pool import ConnectionPool
from brt_platform.exceptions import CollectionCreationError

logger = logging.getLogger(__name__)

VECTOR_DIMENSIONS = {
    "BAAI/bge-large-en-v1.5": 1024,
    "BAAI/bge-base-en-v1.5": 768,
    "intfloat/multilingual-e5-large": 1024,
}

_model = settings.EMBEDDING_MODEL
_vector_size = VECTOR_DIMENSIONS.get(_model)
if _vector_size is None:
    raise ValueError(
        f"Unknown EMBEDDING_MODEL '{_model}'. Known: {list(VECTOR_DIMENSIONS.keys())}"
    )
VECTOR_SIZE = _vector_size


class CollectionManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self._local_locks: dict[str, asyncio.Lock] = {}

    async def get_or_create_collection(self, tenant_id: str) -> str:
        from qdrant_client.models import Distance, VectorParams, SparseVectorParams
        collection_name = f"brt_{tenant_id}"
        client = await ConnectionPool.get_qdrant_client()

        if await client.collection_exists(collection_name):
            return collection_name

        lock_key = f"{RedisKeyPrefix.QDRANT_COLLECTION_LOCK}:{tenant_id}"
        local_lock = self._local_locks.setdefault(tenant_id, asyncio.Lock())

        async with local_lock:
            acquired = await self.redis.set(lock_key, "locked", nx=True, ex=10)
            if not acquired:
                for _ in range(20):
                    await asyncio.sleep(0.5)
                    if await client.collection_exists(collection_name):
                        return collection_name
                raise CollectionCreationError(f"Timed out waiting for '{collection_name}'")

            try:
                if await client.collection_exists(collection_name):
                    return collection_name
                logger.info(f"Creating collection '{collection_name}' (vector_size={VECTOR_SIZE})")
                await client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
                    sparse_vectors_config={"bm25": SparseVectorParams()},
                )
                return collection_name
            except Exception as e:
                if "already exists" in str(e).lower():
                    return collection_name
                raise CollectionCreationError(f"Failed to create '{collection_name}'") from e
            finally:
                await self.redis.delete(lock_key)
