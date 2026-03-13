from typing import cast

import redis

from app.core.config import settings


redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True,
)


def get_original_url_from_cache(short_code: str) -> str | None:
    value = redis_client.get(f"link:{short_code}")
    return cast(str | None, value)


def set_original_url_to_cache(
    short_code: str, original_url: str, ttl: int = 3600
) -> None:
    redis_client.setex(f"link:{short_code}", ttl, original_url)


def delete_link_cache(short_code: str) -> None:
    redis_client.delete(f"link:{short_code}")
