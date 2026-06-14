import asyncio
import logging
from enum import Enum

import aiosqlite

from brt_platform.config import RedisKeyPrefix
from brt_platform.exceptions import CircuitBreakerOpenError

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(self, name: str, redis_client, failure_threshold: int = 3, timeout: float = 30.0):
        self.name = name
        self.redis = redis_client
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.state_key = f"{RedisKeyPrefix.CIRCUIT_BREAKER_STATE}:{name}"
        self.failures_key = f"{RedisKeyPrefix.CIRCUIT_BREAKER_FAILURES}:{name}"

    async def _get_state(self) -> CircuitState:
        val = await self.redis.get(self.state_key)
        return CircuitState(val.decode()) if val else CircuitState.CLOSED

    async def _set_state(self, state: CircuitState, ex: int | None = None):
        await self.redis.set(self.state_key, state.value, ex=ex)

    async def call(self, func, *args, **kwargs):
        state = await self._get_state()
        if state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is OPEN.")
        try:
            result = await func(*args, **kwargs)
            if state in (CircuitState.HALF_OPEN, CircuitState.CLOSED):
                await self.redis.delete(self.failures_key)
                if state == CircuitState.HALF_OPEN:
                    await self._set_state(CircuitState.CLOSED)
                    logger.info(f"Circuit breaker '{self.name}': HALF_OPEN → CLOSED")
            return result
        except Exception as e:
            failures = await self.redis.incr(self.failures_key)
            if failures >= self.failure_threshold:
                await self._set_state(CircuitState.OPEN, ex=int(self.timeout))
                logger.error(f"Circuit breaker '{self.name}': OPEN after {failures} failures")
                asyncio.create_task(self._schedule_half_open())
            raise e

    async def _schedule_half_open(self):
        await asyncio.sleep(self.timeout)
        await self._set_state(CircuitState.HALF_OPEN)
        logger.info(f"Circuit breaker '{self.name}': OPEN → HALF_OPEN")


class OfflineEventBuffer:
    DB_PATH = "/tmp/brt_wal.db"
    _conn = None

    async def _get_conn(self):
        if self._conn is None:
            self._conn = await aiosqlite.connect(self.DB_PATH)
            await self._conn.execute("PRAGMA journal_mode=WAL;")
            await self._conn.execute("""
                CREATE TABLE IF NOT EXISTS event_buffer (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await self._conn.commit()
        return self._conn

    async def capture(self, event_json: str):
        conn = await self._get_conn()
        await conn.execute("INSERT INTO event_buffer (event_json) VALUES (?)", (event_json,))
        await conn.commit()
        logger.debug("Event buffered to SQLite WAL.")

    async def replay(self, replay_func):
        conn = await self._get_conn()
        cursor = await conn.execute("SELECT id, event_json FROM event_buffer ORDER BY id")
        rows = await cursor.fetchall()
        for row_id, event_json in rows:
            try:
                await replay_func(event_json)
                await conn.execute("DELETE FROM event_buffer WHERE id = ?", (row_id,))
            except Exception as e:
                logger.error(f"Replay failed for event {row_id}: {e}")
                break
        await conn.commit()
        logger.info(f"Replayed {len(rows)} buffered events.")
