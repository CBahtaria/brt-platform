import logging
from typing import Any
from brt_platform.config import settings
from brt_platform.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class ConnectionPool:
    _instances: dict[str, Any] = {}

    @classmethod
    async def get_qdrant_client(cls):
        if "qdrant" not in cls._instances:
            from qdrant_client import AsyncQdrantClient
            client = AsyncQdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
                timeout=60.0,
            )
            try:
                await client.health_check()
                cls._instances["qdrant"] = client
                logger.info(f"Qdrant connected: {settings.QDRANT_URL}")
            except Exception as e:
                raise ConfigurationError(f"Cannot connect to Qdrant at {settings.QDRANT_URL}.") from e
        return cls._instances["qdrant"]

    @classmethod
    async def get_redis_client(cls):
        if "redis" not in cls._instances:
            from redis.asyncio import from_url
            client = from_url(settings.REDIS_URL, decode_responses=False)
            await client.ping()
            cls._instances["redis"] = client
            logger.info(f"Redis connected: {settings.REDIS_URL}")
        return cls._instances["redis"]

    @classmethod
    async def close_all(cls):
        for name, client in list(cls._instances.items()):
            try:
                if hasattr(client, 'close'):
                    await client.close()
            except Exception:
                pass
        cls._instances.clear()
        logger.info("All connection pools closed.")
