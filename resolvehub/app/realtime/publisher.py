import json
from typing import Any

from redis.asyncio import Redis

from resolvehub.app.core.config import get_settings


async def publish_json(channel: str, payload: dict[str, Any]) -> None:
    redis = Redis.from_url(get_settings().redis_url)
    try:
        await redis.publish(channel, json.dumps(payload, separators=(",", ":")))
    finally:
        await redis.aclose()
