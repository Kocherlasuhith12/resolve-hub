from hashlib import sha256

from redis.asyncio import Redis
from redis.exceptions import RedisError

from resolvehub.app.core.config import Settings
from resolvehub.app.core.exceptions import AppError


def _login_rate_limit_key(identity: str) -> str:
    """Build a deterministic Redis key without retaining an email address or IP."""
    digest = sha256(identity.encode()).hexdigest()
    return f"resolvehub:auth:login:{digest}"


def _redis_error() -> AppError:
    return AppError("AUTH_TEMPORARILY_UNAVAILABLE", "Authentication is unavailable.", 503)


async def enforce_login_rate_limit(settings: Settings, identity: str) -> None:
    """Reject an identity/IP tuple after five failed attempts in five minutes."""
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    key = _login_rate_limit_key(identity)
    try:
        count = await client.get(key)
        if count is not None and int(count) >= 5:
            raise AppError("RATE_LIMITED", "Too many login attempts. Try again later.", 429)
    except RedisError:
        if settings.environment in {"staging", "production"}:
            raise _redis_error() from None
    finally:
        await client.aclose()


async def record_failed_login(settings: Settings, identity: str) -> None:
    """Record one failed login while preserving the original authentication response."""
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    key = _login_rate_limit_key(identity)
    try:
        count = await client.incr(key)
        if count == 1:
            await client.expire(key, 300)
    except RedisError:
        if settings.environment in {"staging", "production"}:
            raise _redis_error() from None
    finally:
        await client.aclose()


async def reset_login_rate_limit(settings: Settings, identity: str) -> None:
    """Clear prior failures after the identity proves possession of its password."""
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        await client.delete(_login_rate_limit_key(identity))
    except RedisError:
        if settings.environment in {"staging", "production"}:
            raise _redis_error() from None
    finally:
        await client.aclose()
