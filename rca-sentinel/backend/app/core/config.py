"""Typed application settings loaded from environment variables.

All configuration is centralized here. Settings are validated at startup via
Pydantic v2 Settings. No secrets are hard-coded.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(StrEnum):
    """Deployment environment."""

    DEV = "dev"
    DEMO = "demo"
    PROD = "prod"


class Settings(BaseSettings):
    """Application-wide typed settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Application ─────────────────────────────────────────────────
    app_env: AppEnv = AppEnv.DEV
    app_name: str = "rca-sentinel"
    app_version: str = "0.1.0"
    log_level: str = "INFO"
    cors_origins: list[str] | str = Field(default_factory=lambda: ["http://localhost:5173"])
    secret_key: str = "change-me-to-a-random-secret-key"

    # ── Google Cloud Platform ───────────────────────────────────────
    gcp_project_id: str = "project-a8fa4909-225e-4882-b45"
    gcp_location: str = "us-central1"
    spanner_instance_id: str = "rca"
    spanner_database_id: str = "rca-db"
    spanner_graph_name: str = "FactoryGraph"
    pubsub_topic_id: str = "telemetry-ingest-topic"
    pubsub_subscription_id: str = "telemetry-anomaly-sub"
    bigquery_dataset: str = "rca_sentinel"
    bigquery_table: str = "telemetry_historian"
    use_vertex_ai: bool = True

    # ── Neo4j Aura (Legacy / Fallback) ──────────────────────────────
    neo4j_uri: str = "neo4j+s://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = ""
    neo4j_database: str = "neo4j"
    neo4j_max_connection_pool_size: int = 50
    neo4j_connection_timeout: int = 30

    # ── TimescaleDB (Legacy / Fallback) ─────────────────────────────
    timescale_host: str = "timescaledb"
    timescale_port: int = 5432
    timescale_user: str = "rca"
    timescale_password: str = "rca_password"
    timescale_db: str = "rca_sentinel"

    # ── Redis (Legacy / Fallback) ───────────────────────────────────
    redis_url: str = "redis://redis:6379/0"
    redis_max_connections: int = 20

    # ── Google ADK / Vertex AI / Gemini ─────────────────────────────
    google_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_temperature: float = 0.1
    agent_confidence_threshold: float = 0.7

    # ── MCP Server ──────────────────────────────────────────────────
    mcp_server_host: str = "0.0.0.0"
    mcp_server_port: int = 8001
    mcp_auth_token: str = "change-me-mcp-token"

    # ── FastAPI ─────────────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # ── Actuators ───────────────────────────────────────────────────
    dry_run: bool = True
    kill_switch_enabled: bool = False
    actuator_rate_limit: int = 5

    # ── Simulator ───────────────────────────────────────────────────
    simulator_scale: float = 1.0
    simulator_seed: int = 42
    golden_scenario_date: str = "2024-09-15"

    # ── Feature Flags ───────────────────────────────────────────────
    proactive_detection_enabled: bool = False

    # ── JWT ──────────────────────────────────────────────────────────
    jwt_secret_key: str = "change-me-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 480

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def timescale_dsn(self) -> str:
        return (
            f"postgresql://{self.timescale_user}:{self.timescale_password}"
            f"@{self.timescale_host}:{self.timescale_port}/{self.timescale_db}"
        )

    @property
    def is_production(self) -> bool:
        return self.app_env == AppEnv.PROD


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
