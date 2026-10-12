"""JWT authentication and RBAC for RCA-Sentinel.

Simple role-based access: operator, reliability_engineer, quality_engineer, admin.
Approval endpoints require engineer or admin roles. Equipment-affecting actions
always require human approval regardless of role.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import Settings, get_settings
from app.domain.enums import ApproverRole
from app.domain.models import TokenPayload

security_scheme = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Seed users (for demo; production would use a real user store) ───

SEED_USERS: list[dict[str, Any]] = [
    {
        "id": "user-admin-001",
        "username": "admin",
        "password": "admin123",
        "role": "admin",
        "full_name": "System Administrator",
    },
    {
        "id": "user-eng-001",
        "username": "r.engineer",
        "password": "engineer123",
        "role": "reliability_engineer",
        "full_name": "Riley Engineer",
    },
    {
        "id": "user-qe-001",
        "username": "q.engineer",
        "password": "quality123",
        "role": "quality_engineer",
        "full_name": "Quinn Quality",
    },
    {
        "id": "user-op-001",
        "username": "operator",
        "password": "operator123",
        "role": "operator",
        "full_name": "Oscar Operator",
    },
]


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return str(pwd_context.hash(password))


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return bool(pwd_context.verify(plain, hashed))


def create_access_token(
    user_id: str,
    role: ApproverRole,
    settings: Settings | None = None,
) -> str:
    """Create a JWT access token."""
    s = settings or get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=s.jwt_expiration_minutes)
    payload = {
        "sub": user_id,
        "role": role.value,
        "exp": expire,
    }
    return str(jwt.encode(payload, s.jwt_secret_key, algorithm=s.jwt_algorithm))


def decode_token(token: str, settings: Settings | None = None) -> TokenPayload:
    """Decode and validate a JWT token."""
    s = settings or get_settings()
    try:
        payload = jwt.decode(token, s.jwt_secret_key, algorithms=[s.jwt_algorithm])
        return TokenPayload(
            sub=payload["sub"],
            role=ApproverRole(payload["role"]),
            exp=datetime.fromtimestamp(payload["exp"], tz=UTC),
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        ) from exc


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    settings: Settings = Depends(get_settings),
) -> TokenPayload:
    """FastAPI dependency: extract and validate the current user from JWT."""
    return decode_token(credentials.credentials, settings)


def require_role(*allowed_roles: ApproverRole):  # type: ignore[no-untyped-def]
    """FastAPI dependency factory: require the user to have one of the given roles."""

    async def _check(user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' not authorized. Required: {[r.value for r in allowed_roles]}",
            )
        return user

    return _check
