"""Redis client with connection pool, caching, streams, and pub/sub.

All Redis keys are namespaced with 'rca:' prefix. TTLs are always set on cache keys.
Redis is not the source of truth — graph and Postgres are authoritative.
"""

from __future__ import annotations

import json
from typing import Any, cast

import redis.asyncio as aioredis

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RedisClient:
    """Async Redis client wrapper with namespaced keys and helper methods."""

    PREFIX = "rca"

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client: aioredis.Redis[Any] | None = None

    async def connect(self) -> None:
        """Create the Redis connection pool."""
        self._client = aioredis.from_url(
            self._settings.redis_url,
            max_connections=self._settings.redis_max_connections,
            decode_responses=True,
        )
        # Verify connectivity
        await self._client.ping()
        logger.info("redis_connected", url=self._settings.redis_url)

    async def close(self) -> None:
        """Close the Redis connection pool."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("redis_disconnected")

    @property
    def client(self) -> aioredis.Redis[Any]:
        if self._client is None:
            raise RuntimeError("Redis client not initialized. Call connect() first.")
        return self._client

    async def health_check(self) -> bool:
        """Check Redis connectivity."""
        try:
            await self.client.ping()
            return True
        except Exception as exc:
            logger.warning("redis_health_check_failed", error=str(exc))
            return False

    def _key(self, *parts: str) -> str:
        """Build a namespaced key: rca:part1:part2:..."""
        return ":".join([self.PREFIX, *parts])

    # ── Cache operations ────────────────────────────────────────────

    async def cache_get(self, *key_parts: str) -> dict[str, Any] | None:
        """Get a cached JSON value. Returns None on miss."""
        key = self._key("cache", *key_parts)
        raw = await self.client.get(key)
        if raw is None:
            return None
        return json.loads(raw)  # type: ignore[no-any-return]

    async def cache_set(
        self, value: dict[str, Any], *key_parts: str, ttl_seconds: int = 300
    ) -> None:
        """Set a cached JSON value with TTL."""
        key = self._key("cache", *key_parts)
        await self.client.setex(key, ttl_seconds, json.dumps(value, default=str))

    async def cache_invalidate(self, *key_parts: str) -> None:
        """Delete a cache key."""
        key = self._key("cache", *key_parts)
        await self.client.delete(key)

    # ── Stream operations ───────────────────────────────────────────

    async def stream_add(
        self,
        stream_name: str,
        data: dict[str, str],
        maxlen: int = 100000,
    ) -> str:
        """Add a message to a Redis Stream."""
        key = self._key("stream", stream_name)
        msg_id = await self.client.xadd(key, cast("dict[Any, Any]", data), maxlen=maxlen)
        return str(msg_id)

    async def stream_read(
        self,
        stream_name: str,
        last_id: str = "0-0",
        count: int = 100,
        block: int | None = None,
    ) -> list[tuple[str, dict[str, str]]]:
        """Read messages from a Redis Stream."""
        key = self._key("stream", stream_name)
        raw_result: Any = await self.client.xread(
            {key: last_id}, count=count, block=block
        )
        if not raw_result:
            return []
        # result is [[stream_key, [(id, data), ...]]]
        items: list[tuple[str, dict[str, str]]] = []
        for _stream_key, messages in raw_result:
            for item_id, item_data in messages:
                items.append((
                    item_id.decode() if isinstance(item_id, bytes) else str(item_id),
                    {
                        (k.decode() if isinstance(k, bytes) else str(k)): (
                            v.decode() if isinstance(v, bytes) else str(v)
                        )
                        for k, v in item_data.items()
                    },
                ))
        return items

    # ── Pub/Sub operations ──────────────────────────────────────────

    async def publish(self, channel: str, message: dict[str, Any]) -> None:
        """Publish a JSON message to a channel."""
        key = self._key("pubsub", channel)
        await self.client.publish(key, json.dumps(message, default=str))

    # ── Lock operations ─────────────────────────────────────────────

    async def acquire_lock(
        self, resource: str, ttl_seconds: int = 30
    ) -> bool:
        """Try to acquire a distributed lock. Returns True if acquired."""
        key = self._key("lock", resource)
        acquired = await self.client.set(key, "1", nx=True, ex=ttl_seconds)
        return bool(acquired)

    async def release_lock(self, resource: str) -> None:
        """Release a distributed lock."""
        key = self._key("lock", resource)
        await self.client.delete(key)

    # ── Idempotency keys ────────────────────────────────────────────

    async def check_idempotency(self, key: str, ttl_seconds: int = 3600) -> bool:
        """Check if an operation was already processed. Returns True if new."""
        idem_key = self._key("idem", key)
        result = await self.client.set(idem_key, "1", nx=True, ex=ttl_seconds)
        return bool(result)


# Module-level singleton
_redis_client: RedisClient | None = None


def get_redis_client() -> RedisClient:
    """Get the module-level Redis client singleton."""
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized.")
    return _redis_client


async def init_redis_client(settings: Settings | None = None) -> RedisClient:
    """Initialize and return the module-level Redis client."""
    global _redis_client
    _redis_client = RedisClient(settings)
    await _redis_client.connect()
    return _redis_client


async def close_redis_client() -> None:
    """Close the module-level Redis client."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
