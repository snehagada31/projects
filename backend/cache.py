"""
Topic 13 — @cache_feed(ttl=30) decorator.
Caches async results per (cursor, limit) key for `ttl` seconds.
"""

import time
import functools


def cache_feed(ttl=30):
    def decorator(func):
        cache = {}

        @functools.wraps(func)
        async def wrapper(cursor, limit):
            key = (cursor, limit)
            now = time.time()

            if key in cache:
                result, cached_at = cache[key]
                if now - cached_at < ttl:
                    print(f"[cache HIT] cursor={cursor}")
                    return result

            print(f"[cache MISS] cursor={cursor}")
            result = await func(cursor, limit)
            cache[key] = (result, now)
            return result

        return wrapper
    return decorator