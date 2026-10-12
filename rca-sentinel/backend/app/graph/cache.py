"""Redis-backed query caching for Neo4j Cypher and analytics queries."""

from __future__ import annotations

import functools
import hashlib
import json
from typing import Any, Callable, Coroutine

from app.core.logging import get_logger
from app.core.redis import get_redis_client

logger = get_logger(__name__)


def cached_graph_query(
    ttl_seconds: int = 60,
    prefix: str = "graph_cache",
) -> Callable[..., Any]:
    """Decorator to cache async graph query results in Redis."""

    def decorator(
        func: Callable[..., Coroutine[Any, Any, Any]],
    ) -> Callable[..., Coroutine[Any, Any, Any]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate cache key from func name and arguments
            arg_str = json.dumps(
                {"args": [str(a) for a in args[1:]], "kwargs": {k: str(v) for k, v in kwargs.items()}},
                sort_keys=True,
            )
            arg_hash = hashlib.sha256(arg_str.encode()).hexdigest()[:16]
            cache_key = f"{prefix}:{func.__name__}:{arg_hash}"

            try:
                redis = get_redis_client()
                cached_val = await redis.get(cache_key)
                if cached_val is not None:
                    return cached_val
            except Exception:
                # Redis cache miss or disconnected, proceed to function execution
                pass

            result = await func(*args, **kwargs)

            try:
                redis = get_redis_client()
                await redis.set(cache_key, result, ttl_seconds=ttl_seconds)
            except Exception:
                pass

            return result

        return wrapper

    return decorator
