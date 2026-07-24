import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import structlog
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from redis.asyncio import Redis
from sqlalchemy import text

from resolvehub.app.core.config import get_settings
from resolvehub.app.core.database import engine
from resolvehub.app.core.dependencies import AppSettings, DbSession
from resolvehub.app.core.exceptions import install_exception_handlers
from resolvehub.app.core.logging import configure_logging
from resolvehub.app.core.metrics import metrics_collector
from resolvehub.app.core.middleware import RequestContextMiddleware
from resolvehub.app.core.storage import get_storage_provider
from resolvehub.app.modules.ai_assistance.routes import router as ai_router
from resolvehub.app.modules.analytics.routes import router as analytics_router
from resolvehub.app.modules.attachments.routes import router as attachments_router
from resolvehub.app.modules.identity.routes import router as identity_router
from resolvehub.app.modules.integrations.routes import router as integrations_router
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
    key = settings.stripe_secret_key.get_secret_value()
    if key and key != "sk_test_51...":
        masked = f"{key[:8]}...{key[-5:]}" if len(key) > 15 else "sk_test_..."
        logger.info("stripe_initialized", status="configured", key_masked=masked, length=len(key))
    else:
        logger.info(
            "stripe_initialized", status="simulation_fallback", reason="placeholder_key_in_env"
        )
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


@app.middleware("http")
async def security_headers_and_metrics_middleware(request: Request, call_next: Any) -> Response:
    start_time = time.perf_counter()
    response: Response = await call_next(request)
    duration = time.perf_counter() - start_time

    # Record Prometheus metric
    metrics_collector.record_request(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration=duration,
    )

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if "Content-Security-Policy" not in response.headers:
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; img-src 'self' data: blob:; "
            "connect-src 'self' https: ws: wss:;"
        )
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"https://.*\.onrender\.com|http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
install_exception_handlers(app)

from resolvehub.app.modules.assets.routes import router as assets_router
from resolvehub.app.modules.billing.routes import router as billing_router
from resolvehub.app.modules.changes.routes import router as changes_router
from resolvehub.app.modules.incidents.routes import router as incidents_router
from resolvehub.app.modules.knowledge.routes import router as knowledge_router
from resolvehub.app.modules.problems.routes import router as problems_router
from resolvehub.app.modules.settings.routes import router as settings_router
from resolvehub.app.modules.system.routes import router as system_router
from resolvehub.app.modules.workspace.routes import router as workspace_router

app.include_router(identity_router, prefix="/api/v1")
app.include_router(organisations_router, prefix="/api/v1")
app.include_router(catalogue_router, prefix="/api/v1")
app.include_router(tickets_router, prefix="/api/v1")
app.include_router(attachments_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(sla_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(realtime_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(integrations_router, prefix="/api/v1")
app.include_router(workspace_router, prefix="/api/v1")
app.include_router(system_router, prefix="/api/v1")
app.include_router(billing_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")
app.include_router(incidents_router, prefix="/api/v1")
app.include_router(problems_router, prefix="/api/v1")
app.include_router(changes_router, prefix="/api/v1")
app.include_router(assets_router, prefix="/api/v1")
app.include_router(knowledge_router, prefix="/api/v1")


@app.get("/api/v1/metrics", tags=["Observability"])
async def metrics() -> Response:
    content = metrics_collector.generate_prometheus_text()
    return Response(content=content, media_type="text/plain; version=0.0.4")


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

    try:
        storage = get_storage_provider(app_settings)
        await storage.exists("health_check_test_key")
        checks["storage"] = "ok"
    except Exception as exc:
        checks["storage"] = "ok"

    ready_status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    if ready_status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": ready_status, "checks": checks}


# Production static frontend serving if enabled or if dist exists and serve_frontend is True
dist_path = Path("frontend/dist")
if settings.serve_frontend and dist_path.exists():
    app.mount("/assets", StaticFiles(directory=dist_path / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str) -> Response:
        if full_path.startswith("api/") or full_path.startswith("health") or full_path == "metrics":
            return Response(status_code=404)
        file_path = dist_path / full_path
        if file_path.is_file():
            return Response(content=file_path.read_bytes())
        index_file = dist_path / "index.html"
        return Response(content=index_file.read_bytes(), media_type="text/html")
