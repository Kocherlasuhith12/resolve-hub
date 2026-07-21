from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from sqlalchemy import text

from resolvehub.app.core.config import get_settings
from resolvehub.app.core.database import engine
from resolvehub.app.core.dependencies import AppSettings, DbSession
from resolvehub.app.core.exceptions import install_exception_handlers
from resolvehub.app.core.logging import configure_logging
from resolvehub.app.core.middleware import RequestContextMiddleware
from resolvehub.app.modules.ai_assistance.routes import router as ai_router
from resolvehub.app.modules.identity.routes import router as identity_router
from resolvehub.app.modules.notifications.routes import router as notifications_router
from resolvehub.app.modules.organisations.routes import router as organisations_router
from resolvehub.app.modules.search.routes import router as search_router
from resolvehub.app.modules.service_catalogue.routes import router as catalogue_router
from resolvehub.app.modules.sla.routes import router as sla_router
from resolvehub.app.modules.tickets.routes import router as tickets_router
from resolvehub.app.realtime.routes import router as realtime_router

settings = get_settings()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await engine.dispose()


configure_logging()
app = FastAPI(
    title="ResolveHub API",
    version="0.1.0",
    description="Multi-tenant service request and operations platform",
    lifespan=lifespan,
)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-CSRF-Token",
        "X-Organisation-ID",
        "X-Request-ID",
        "X-ResolveHub-Client",
    ],
)
install_exception_handlers(app)
app.include_router(identity_router, prefix="/api/v1")
app.include_router(organisations_router, prefix="/api/v1")
app.include_router(catalogue_router, prefix="/api/v1")
app.include_router(tickets_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(sla_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(realtime_router, prefix="/api/v1")


@app.get("/health/live", tags=["Health"])
async def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready", tags=["Health"])
async def ready(
    response: Response, session: DbSession, app_settings: AppSettings
) -> dict[str, Any]:
    checks: dict[str, str] = {}
    try:
        await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = "unavailable"
        logger.warning(
            "readiness_check_failed", dependency="database", error_type=type(exc).__name__
        )
    redis = Redis.from_url(app_settings.redis_url)
    try:
        await redis.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = "unavailable"
        logger.warning("readiness_check_failed", dependency="redis", error_type=type(exc).__name__)
    finally:
        await redis.aclose()
    ready_status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    if ready_status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": ready_status, "checks": checks}
