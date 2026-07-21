from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from resolvehub.app.core.config import Settings, get_settings
from resolvehub.app.core.database import get_db
from resolvehub.app.core.exceptions import AppError
from resolvehub.app.core.security import decode_access_token
from resolvehub.app.modules.identity.models import AuthSession, User

bearer = HTTPBearer(auto_error=False)
DbSession = Annotated[AsyncSession, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


@dataclass(frozen=True)
class Principal:
    user: User
    session_id: UUID


async def get_principal(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    session: DbSession,
    settings: AppSettings,
) -> Principal:
    if credentials is None or credentials.scheme.casefold() != "bearer":
        raise AppError("AUTHENTICATION_REQUIRED", "Authentication is required.", 401)
    try:
        user_id, session_id = decode_access_token(credentials.credentials, settings)
    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise AppError("ACCESS_TOKEN_INVALID", "Access token is invalid or expired.", 401) from None
    auth_session = await session.scalar(
        select(AuthSession).where(
            AuthSession.id == session_id,
            AuthSession.user_id == user_id,
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > datetime.now(UTC),
        )
    )
    user = await session.get(User, user_id)
    if auth_session is None or user is None or not user.is_active:
        raise AppError("ACCESS_TOKEN_INVALID", "Access token is invalid or expired.", 401)
    return Principal(user=user, session_id=session_id)


CurrentPrincipal = Annotated[Principal, Depends(get_principal)]
