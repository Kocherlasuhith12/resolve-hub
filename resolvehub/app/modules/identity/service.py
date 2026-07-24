from datetime import UTC, datetime, timedelta
from hmac import compare_digest
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from resolvehub.app.core.config import Settings
from resolvehub.app.core.exceptions import AppError
from resolvehub.app.core.security import (
    create_access_token,
    generate_opaque_token,
    hash_opaque_token,
    hash_password,
    verify_password,
)
from resolvehub.app.modules.identity.models import AuthSession, User

_DUMMY_PASSWORD_HASH = hash_password(generate_opaque_token())


def authentication_failed() -> AppError:
    """Return a fresh exception so concurrent requests never reuse traceback state."""
    return AppError("AUTHENTICATION_FAILED", "Invalid email or password.", 401)


def normalize_email(email: str) -> str:
    return email.strip().casefold()


async def register_user(
    session: AsyncSession, *, email: str, password: str, display_name: str, settings: Settings
) -> tuple[User | None, str | None]:
    normalized = normalize_email(email)
    existing = await session.scalar(select(User).where(User.email == normalized))
    if existing:
        return None, None
    raw_token = generate_opaque_token()
    user = User(
        email=normalized,
        password_hash=hash_password(password),
        display_name=display_name.strip(),
        is_email_verified=True,
        verification_token_hash=hash_opaque_token(raw_token),
        verification_expires_at=datetime.now(UTC)
        + timedelta(hours=settings.email_verification_ttl_hours),
    )
    session.add(user)
    await session.commit()
    return user, raw_token


async def verify_email(session: AsyncSession, token: str) -> None:
    now = datetime.now(UTC)
    user = await session.scalar(
        select(User).where(
            User.verification_token_hash == hash_opaque_token(token),
            User.verification_expires_at > now,
        )
    )
    if user is None:
        raise AppError(
            "VERIFICATION_TOKEN_INVALID", "Verification token is invalid or expired.", 400
        )
    user.is_email_verified = True
    user.verification_token_hash = None
    user.verification_expires_at = None
    await session.commit()


async def authenticate(session: AsyncSession, email: str, password: str) -> User:
    user = await session.scalar(select(User).where(User.email == normalize_email(email)))
    candidate_hash = user.password_hash if user is not None else _DUMMY_PASSWORD_HASH
    password_matches = verify_password(password, candidate_hash)
    if user is None or not password_matches:
        raise authentication_failed()
    if not user.is_active or not user.is_email_verified:
        raise authentication_failed()
    return user


async def create_session(
    session: AsyncSession,
    *,
    user: User,
    settings: Settings,
    user_agent: str | None,
    ip_address: str | None,
    family_id: UUID | None = None,
    csrf_token_hash: str | None = None,
) -> tuple[str, str, AuthSession]:
    now = datetime.now(UTC)
    raw_refresh = generate_opaque_token()
    auth_session = AuthSession(
        user_id=user.id,
        family_id=family_id or uuid4(),
        refresh_token_hash=hash_opaque_token(raw_refresh),
        csrf_token_hash=csrf_token_hash,
        created_at=now,
        expires_at=now + timedelta(days=settings.refresh_token_ttl_days),
        user_agent=user_agent,
        ip_address=ip_address,
    )
    session.add(auth_session)
    await session.flush()
    access = create_access_token(user_id=user.id, session_id=auth_session.id, settings=settings)
    return access, raw_refresh, auth_session


async def rotate_refresh_token(
    session: AsyncSession,
    *,
    token: str,
    settings: Settings,
    user_agent: str | None,
    ip_address: str | None,
    csrf_token: str | None = None,
    replacement_csrf_token_hash: str | None = None,
) -> tuple[str, str]:
    now = datetime.now(UTC)
    current = await session.scalar(
        select(AuthSession)
        .where(AuthSession.refresh_token_hash == hash_opaque_token(token))
        .with_for_update()
    )
    if current is None or current.expires_at <= now:
        raise AppError("REFRESH_TOKEN_INVALID", "Refresh token is invalid or expired.", 401)
    if csrf_token is not None and (
        current.csrf_token_hash is None
        or not compare_digest(current.csrf_token_hash, hash_opaque_token(csrf_token))
    ):
        raise AppError("CSRF_TOKEN_INVALID", "CSRF token is invalid.", 403)
    if current.rotated_at or current.revoked_at:
        await session.execute(
            update(AuthSession)
            .where(AuthSession.family_id == current.family_id, AuthSession.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await session.commit()
        raise AppError("REFRESH_TOKEN_REUSED", "Refresh token reuse was detected.", 401)
    user = await session.get(User, current.user_id)
    if user is None or not user.is_active:
        raise AppError("REFRESH_TOKEN_INVALID", "Refresh token is invalid or expired.", 401)
    access, refresh, replacement = await create_session(
        session,
        user=user,
        settings=settings,
        user_agent=user_agent,
        ip_address=ip_address,
        family_id=current.family_id,
        csrf_token_hash=replacement_csrf_token_hash,
    )
    current.rotated_at = now
    current.replaced_by_id = replacement.id
    await session.commit()
    return access, refresh


async def revoke_session(session: AsyncSession, session_id: UUID, user_id: UUID) -> None:
    auth_session = await session.scalar(
        select(AuthSession).where(AuthSession.id == session_id, AuthSession.user_id == user_id)
    )
    if auth_session is None:
        raise AppError("SESSION_NOT_FOUND", "Session was not found.", 404)
    auth_session.revoked_at = auth_session.revoked_at or datetime.now(UTC)
    await session.commit()
