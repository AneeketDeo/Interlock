"""FastAPI application entry point.

Configures lifespan (connect/disconnect all clients), CORS, exception handlers,
and mounts all routers under /api/v1.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import close_timescale_client, init_timescale_client
from app.core.errors import (
    ApprovalRequired,
    AuthenticationError,
    AuthorizationError,
    GraphConnectionError,
    GraphQueryError,
    KillSwitchActive,
    NotFoundError,
    PolicyViolation,
    RcaError,
    ValidationRejected,
)
from app.core.logging import get_logger, setup_logging
from app.core.redis import close_redis_client, init_redis_client
from app.graph.client import close_neo4j_client, init_neo4j_client

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: initialize and close all clients."""
    setup_logging()
    settings = get_settings()
    logger.info(
        "app_starting",
        app_name=settings.app_name,
        version=settings.app_version,
        env=settings.app_env,
    )

    # Initialize clients
    try:
        await init_neo4j_client(settings)
    except GraphConnectionError:
        logger.error("neo4j_connection_failed_at_startup")
        # Allow startup to continue for local dev without Aura
        if settings.app_env == "prod":
            raise

    try:
        await init_redis_client(settings)
    except Exception:
        logger.error("redis_connection_failed_at_startup")
        if settings.app_env == "prod":
            raise

    try:
        await init_timescale_client(settings)
    except Exception:
        logger.error("timescaledb_connection_failed_at_startup")
        if settings.app_env == "prod":
            raise

    logger.info("app_started")
    yield

    # Shutdown
    await close_neo4j_client()
    await close_redis_client()
    await close_timescale_client()
    logger.info("app_stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="RCA-Sentinel API",
        description="Agentic knowledge-graph-driven Root Cause Analysis platform",
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    _register_exception_handlers(app)

    # Mount routers
    from app.api.health import router as health_router
    from app.api.ingestion import router as ingestion_router

    app.include_router(health_router, tags=["Health"])
    app.include_router(ingestion_router, prefix="/api/v1")

    return app


def _register_exception_handlers(app: FastAPI) -> None:
    """Register domain exception to HTTP response mappings."""

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"code": "NOT_FOUND", "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(ValidationRejected)
    async def validation_handler(request: Request, exc: ValidationRejected) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"code": "VALIDATION_REJECTED", "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(GraphConnectionError)
    async def graph_conn_handler(request: Request, exc: GraphConnectionError) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={"code": "GRAPH_UNAVAILABLE", "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(GraphQueryError)
    async def graph_query_handler(request: Request, exc: GraphQueryError) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"code": "GRAPH_QUERY_ERROR", "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(PolicyViolation)
    async def policy_handler(request: Request, exc: PolicyViolation) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={"code": "POLICY_VIOLATION", "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(ApprovalRequired)
    async def approval_handler(request: Request, exc: ApprovalRequired) -> JSONResponse:
        return JSONResponse(
            status_code=202,
            content={
                "code": "APPROVAL_REQUIRED",
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(KillSwitchActive)
    async def kill_switch_handler(request: Request, exc: KillSwitchActive) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={"code": "KILL_SWITCH_ACTIVE", "message": exc.message},
        )

    @app.exception_handler(AuthenticationError)
    async def auth_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={"code": "AUTHENTICATION_ERROR", "message": exc.message},
        )

    @app.exception_handler(AuthorizationError)
    async def authz_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={"code": "AUTHORIZATION_ERROR", "message": exc.message},
        )

    @app.exception_handler(RcaError)
    async def rca_error_handler(request: Request, exc: RcaError) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"code": "INTERNAL_ERROR", "message": exc.message, "details": exc.details},
        )


# Create the app instance
app = create_app()
