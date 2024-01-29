import asyncio
from datetime import timedelta
from typing import Any, Callable
from diskcache import Cache
from diskcache.core import full_name, args_to_key, ENOVAL
from functools import lru_cache, partial, wraps

from jinja2 import BytecodeCache as BaseBytecodeCache
from jinja2.bccache import Bucket

from juniorguru.lib import loggers


CACHE_DIR = ".cache"


logger = loggers.from_path(__file__)

_cache_instances = {}


def get_cache(cache_dir=CACHE_DIR) -> Cache:
    try:
        cache = _cache_instances[cache_dir]
    except KeyError:
        logger.debug(f"Initializing cache: {cache_dir}")
        cache = _cache_instances[cache_dir] = Cache(cache_dir)
    return cache


def close_cache() -> None:
    if caches := _cache_instances.values():
        logger.debug("Cache clean up")
        for cache in caches:
            cache.expire()
            cache.close()


def pass_cache(fn: Callable) -> Callable:
    @wraps(fn)
    def wrapper(*args, **kwargs) -> Any:
        kwargs.setdefault("cache", get_cache())
        return fn(*args, **kwargs)

    return wrapper


def cache(
    expire: float | int | timedelta | None = None,
    tag: str | None = None,
    ignore: tuple[int | str] = (),
) -> Callable:
    if isinstance(expire, timedelta):
        expire = expire.total_seconds()

    def decorator(fn: Callable) -> Callable:
        cache = get_cache()

        # Rewriting subset of diskcache.memoize() to support async
        if asyncio.iscoroutinefunction(fn):
            base = (full_name(fn),)

            @wraps(fn)
            async def wrapper(*args, **kwargs) -> Any:
                key = args_to_key(base, args, kwargs, False, ignore)
                result = await _call_async(cache.get, key, default=ENOVAL, retry=True)

                if result is ENOVAL:
                    result = await fn(*args, **kwargs)
                    if expire is None or expire > 0:
                        await _call_async(
                            cache.set, key, result, expire, tag=tag, retry=True
                        )

                return result

            return wrapper

        # For sync functions, we can use diskcache.memoize() directly
        return cache.memoize(expire=expire, tag=tag, ignore=ignore)(fn)

    return decorator


class BytecodeCache(BaseBytecodeCache):
    def __init__(self, cache: Cache):
        self.cache = cache

    def load_bytecode(self, bucket: Bucket):
        with self.cache.read(f"jinja:{bucket.key}") as f:
            bucket.load_bytecode(f)

    def dump_bytecode(self, bucket: Bucket):
        self.cache.set(f"jinja:{bucket.key}", bucket.bytecode_to_string(), tag="jinja")


@lru_cache()
def get_jinja_cache() -> BytecodeCache:
    return BytecodeCache(get_cache())


def _call_async(fn, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(None, partial(fn, *args, **kwargs))
