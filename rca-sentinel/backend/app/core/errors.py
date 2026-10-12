"""Domain exception hierarchy.

Every domain error maps to a specific HTTP status via the exception handlers
in app/api/errors.py. Catch specific exceptions only; never except Exception: pass.
"""

from __future__ import annotations

from typing import Any


class RcaError(Exception):
    """Base exception for all RCA-Sentinel domain errors."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class GraphQueryError(RcaError):
    """Error executing a graph query against Neo4j."""


class GraphConnectionError(RcaError):
    """Cannot connect to Neo4j Aura instance (unreachable or paused)."""


class ValidationRejected(RcaError):
    """Data failed SHACL or Pydantic validation; sent to quarantine."""


class EntityResolutionError(RcaError):
    """Failed to resolve an entity across source systems."""


class IngestionError(RcaError):
    """Error during data ingestion pipeline execution."""


class PolicyViolation(RcaError):
    """Action violates the remediation policy engine rules."""


class ApprovalRequired(RcaError):
    """Action requires human approval before execution."""

    def __init__(self, message: str, *, approval_id: str, action_type: str) -> None:
        super().__init__(message, details={"approval_id": approval_id, "action_type": action_type})
        self.approval_id = approval_id
        self.action_type = action_type


class ApprovalNotFound(RcaError):
    """Referenced approval record does not exist."""


class KillSwitchActive(RcaError):
    """Global kill switch is enabled; no actuator actions allowed."""


class ActuatorError(RcaError):
    """Error executing an actuator action (interlock, ERP, CMMS)."""


class AuthenticationError(RcaError):
    """Authentication failure (bad credentials, expired token)."""


class AuthorizationError(RcaError):
    """User lacks the required role for this operation."""


class AgentError(RcaError):
    """Error within the ADK agent pipeline."""


class ConfidenceBelowThreshold(AgentError):
    """Agent confidence is below the configured threshold; escalate to human."""

    def __init__(self, message: str, *, confidence: float, threshold: float) -> None:
        super().__init__(
            message, details={"confidence": confidence, "threshold": threshold}
        )
        self.confidence = confidence
        self.threshold = threshold


class GroundingError(AgentError):
    """Agent claim is not grounded in graph evidence."""


class NotFoundError(RcaError):
    """Requested resource was not found."""


class ConflictError(RcaError):
    """Operation conflicts with existing state (duplicate, version mismatch)."""
