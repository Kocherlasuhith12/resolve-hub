from datetime import UTC, datetime
from hmac import compare_digest
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Cookie, Header, Request, Response, status
from sqlalchemy import select, update

from resolvehub.app.core.dependencies import AppSettings, CurrentPrincipal, DbSession
from resolvehub.app.core.exceptions import AppError
from resolvehub.app.core.rate_limit import (
    enforce_login_rate_limit,
    record_failed_login,
    reset_login_rate_limit,
)
from resolvehub.app.core.security import generate_opaque_token, hash_opaque_token
from resolvehub.app.modules.identity.models import AuthSession
from resolvehub.app.modules.identity.schemas import (
    BrowserTokenResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    SessionResponse,
    TokenPair,
    UserResponse,
    VerifyEmailRequest,
)
from resolvehub.app.modules.identity.service import (
    authenticate,
    create_session,
    register_user,
    revoke_session,
    rotate_refresh_token,
    verify_email,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

_BROWSER_REFRESH_COOKIE = "resolvehub_refresh"
_BROWSER_CSRF_COOKIE = "resolvehub_csrf"
_BROWSER_COOKIE_PATH = "/api/v1/auth/browser"


def _client_metadata(request: Request, user_agent: str | None) -> tuple[str | None, str | None]:
    return user_agent, request.client.host if request.client else None


def _require_browser_client(value: str | None) -> None:
    if value != "browser":
        raise AppError("BROWSER_CLIENT_HEADER_REQUIRED", "Browser client header is required.", 400)


def _set_browser_cookies(
    response: Response, *, refresh_token: str, csrf_token: str, settings: AppSettings
) -> None:
    max_age = settings.refresh_token_ttl_days * 24 * 60 * 60
    response.set_cookie(
        _BROWSER_REFRESH_COOKIE,
        refresh_token,
        max_age=max_age,
        path=_BROWSER_COOKIE_PATH,
        secure=settings.browser_cookie_secure,
        httponly=True,
        samesite="lax",
    )
    response.set_cookie(
        _BROWSER_CSRF_COOKIE,
        csrf_token,
        max_age=max_age,
        path="/",
        secure=settings.browser_cookie_secure,
        httponly=False,
        samesite="lax",
    )


def _clear_browser_cookies(response: Response, settings: AppSettings) -> None:
    response.delete_cookie(
        _BROWSER_REFRESH_COOKIE,
        path=_BROWSER_COOKIE_PATH,
        secure=settings.browser_cookie_secure,
        httponly=True,
        samesite="lax",
    )
    response.delete_cookie(
        _BROWSER_CSRF_COOKIE,
        path="/",
        secure=settings.browser_cookie_secure,
        httponly=False,
        samesite="lax",
    )


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Register an account",
    description=(
        "Creates an account and starts email verification. Email verification is required before "
        "login. For enumeration resistance this endpoint always returns the same accepted "
        "response; "
        "a verification token is included only for a newly registered account in local/test mode."
    ),
)
async def register(
    payload: RegisterRequest, session: DbSession, settings: AppSettings
) -> RegisterResponse:
    _, token = await register_user(
        session,
        email=str(payload.email),
        password=payload.password,
        display_name=payload.display_name,
        settings=settings,
    )
    return RegisterResponse(
        message="If the address can be registered, verification instructions will be sent.",
        verification_token=token if settings.environment in {"local", "test"} else None,
    )


@router.post(
    "/verify-email",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Verify an email address before login",
)
async def verify(payload: VerifyEmailRequest, session: DbSession) -> Response:
    await verify_email(session, payload.token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/login",
    response_model=TokenPair,
    summary="Log in to a verified account",
    description=(
        "Returns access and refresh tokens for an active, email-verified account. All invalid "
        "credentials and unavailable accounts use the same response to prevent account enumeration."
    ),
)
async def login(
    payload: LoginRequest,
    request: Request,
    session: DbSession,
    settings: AppSettings,
    user_agent: Annotated[str | None, Header()] = None,
) -> TokenPair:
    ip = request.client.host if request.client else "unknown"
    rate_limit_identity = f"{ip}:{str(payload.email).casefold()}"
    await enforce_login_rate_limit(settings, rate_limit_identity)
    try:
        user = await authenticate(session, str(payload.email), payload.password)
    except AppError as exc:
        if exc.code == "AUTHENTICATION_FAILED":
            await record_failed_login(settings, rate_limit_identity)
        raise
    await reset_login_rate_limit(settings, rate_limit_identity)
    access, refresh, _ = await create_session(
        session,
        user=user,
        settings=settings,
        user_agent=user_agent,
        ip_address=ip,
    )
    await session.commit()
    return TokenPair(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.access_token_ttl_minutes * 60,
    )


@router.post(
    "/browser/login",
    response_model=BrowserTokenResponse,
    summary="Log in from the ResolveHub browser application",
)
async def browser_login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    session: DbSession,
    settings: AppSettings,
    user_agent: Annotated[str | None, Header()] = None,
    browser_client: Annotated[str | None, Header(alias="X-ResolveHub-Client")] = None,
) -> BrowserTokenResponse:
    _require_browser_client(browser_client)
    ip = request.client.host if request.client else "unknown"
    rate_limit_identity = f"{ip}:{str(payload.email).casefold()}"
    await enforce_login_rate_limit(settings, rate_limit_identity)
    try:
        user = await authenticate(session, str(payload.email), payload.password)
    except AppError as exc:
        if exc.code == "AUTHENTICATION_FAILED":
            await record_failed_login(settings, rate_limit_identity)
        raise
    await reset_login_rate_limit(settings, rate_limit_identity)
    csrf_token = generate_opaque_token()
    access, refresh_value, _ = await create_session(
        session,
        user=user,
        settings=settings,
        user_agent=user_agent,
        ip_address=ip,
        csrf_token_hash=hash_opaque_token(csrf_token),
    )
    await session.commit()
    _set_browser_cookies(
        response,
        refresh_token=refresh_value,
        csrf_token=csrf_token,
        settings=settings,
    )
    return BrowserTokenResponse(
        access_token=access,
        csrf_token=csrf_token,
        expires_in=settings.access_token_ttl_minutes * 60,
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    payload: RefreshRequest,
    request: Request,
    session: DbSession,
    settings: AppSettings,
    user_agent: Annotated[str | None, Header()] = None,
) -> TokenPair:
    user_agent_value, ip = _client_metadata(request, user_agent)
    access, refresh_value = await rotate_refresh_token(
        session,
        token=payload.refresh_token,
        settings=settings,
        user_agent=user_agent_value,
        ip_address=ip,
    )
    return TokenPair(
        access_token=access,
        refresh_token=refresh_value,
        expires_in=settings.access_token_ttl_minutes * 60,
    )


@router.post(
    "/browser/refresh",
    response_model=BrowserTokenResponse,
    summary="Rotate a browser session using protected cookies",
)
async def browser_refresh(
    request: Request,
    response: Response,
    session: DbSession,
    settings: AppSettings,
    refresh_cookie: Annotated[str | None, Cookie(alias=_BROWSER_REFRESH_COOKIE)] = None,
    csrf_cookie: Annotated[str | None, Cookie(alias=_BROWSER_CSRF_COOKIE)] = None,
    csrf_header: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
    browser_client: Annotated[str | None, Header(alias="X-ResolveHub-Client")] = None,
    user_agent: Annotated[str | None, Header()] = None,
) -> BrowserTokenResponse:
    _require_browser_client(browser_client)
    if (
        refresh_cookie is None
        or csrf_cookie is None
        or csrf_header is None
        or not compare_digest(csrf_cookie, csrf_header)
    ):
        raise AppError("CSRF_TOKEN_INVALID", "CSRF token is invalid.", 403)
    next_csrf = generate_opaque_token()
    user_agent_value, ip = _client_metadata(request, user_agent)
    access, next_refresh = await rotate_refresh_token(
        session,
        token=refresh_cookie,
        settings=settings,
        user_agent=user_agent_value,
        ip_address=ip,
        csrf_token=csrf_header,
        replacement_csrf_token_hash=hash_opaque_token(next_csrf),
    )
    _set_browser_cookies(
        response,
        refresh_token=next_refresh,
        csrf_token=next_csrf,
        settings=settings,
    )
    return BrowserTokenResponse(
        access_token=access,
        csrf_token=next_csrf,
        expires_in=settings.access_token_ttl_minutes * 60,
    )


@router.get("/me", response_model=UserResponse)
async def me(principal: CurrentPrincipal) -> UserResponse:
    return UserResponse.model_validate(principal.user)


@router.get("/sessions", response_model=list[SessionResponse])
async def sessions(principal: CurrentPrincipal, session: DbSession) -> list[SessionResponse]:
    result = await session.scalars(
        select(AuthSession)
        .where(AuthSession.user_id == principal.user.id)
        .order_by(AuthSession.created_at.desc())
        .limit(100)
    )
    return [SessionResponse.model_validate(item) for item in result]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID, principal: CurrentPrincipal, session: DbSession
) -> Response:
    await revoke_session(session, session_id, principal.user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(principal: CurrentPrincipal, session: DbSession) -> Response:
    await revoke_session(session, principal.session_id, principal.user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/browser/logout", status_code=status.HTTP_204_NO_CONTENT)
async def browser_logout(
    principal: CurrentPrincipal, session: DbSession, settings: AppSettings
) -> Response:
    await revoke_session(session, principal.session_id, principal.user.id)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    _clear_browser_cookies(response, settings)
    return response


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(principal: CurrentPrincipal, session: DbSession) -> Response:
    await session.execute(
        update(AuthSession)
        .where(AuthSession.user_id == principal.user.id, AuthSession.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
