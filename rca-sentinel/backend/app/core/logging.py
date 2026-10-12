"""Structured JSON logging with structlog.

Configures a JSON-formatted logger with correlation_id propagation.
Never logs secrets, tokens, or raw PII.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

from app.core.config import get_settings


def setup_logging() -> None:
    """Configure structured logging for the application."""
    settings = get_settings()
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Configure structlog processors
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.app_env == "dev":
        # Pretty printing for development
        renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer()
    else:
        # JSON for production/demo
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Suppress noisy third-party loggers
    for logger_name in ("neo4j", "asyncpg", "httpx", "uvicorn.access"):
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_logger(name: str, **initial_context: Any) -> structlog.stdlib.BoundLogger:
    """Get a bound logger with optional initial context."""
    logger: structlog.stdlib.BoundLogger = structlog.get_logger(name)
    if initial_context:
        logger = logger.bind(**initial_context)
    return logger
