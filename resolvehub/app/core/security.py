import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
from pwdlib import PasswordHash

from resolvehub.app.core.config import Settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    return password_hash.verify(password, encoded)


def generate_opaque_token() -> str:
    return secrets.token_urlsafe(48)


def hash_opaque_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(*, user_id: UUID, session_id: UUID, settings: Settings) -> str:
    now = datetime.now(UTC)
    claims: dict[str, Any] = {
        "sub": str(user_id),
        "sid": str(session_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_ttl_minutes),
    }
    return jwt.encode(
        claims, settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm
    )


def decode_access_token(token: str, settings: Settings) -> tuple[UUID, UUID]:
    claims = jwt.decode(
        token, settings.jwt_secret.get_secret_value(), algorithms=[settings.jwt_algorithm]
    )
    if claims.get("type") != "access":
        raise jwt.InvalidTokenError("invalid token type")
    return UUID(claims["sub"]), UUID(claims["sid"])
