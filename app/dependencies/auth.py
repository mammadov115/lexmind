import uuid
from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.repositories.user import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials.",
    headers={"WWW-Authenticate": "Bearer"},
)


@dataclass(frozen=True)
class CurrentUser:
    """Immutable snapshot of the authenticated user carried per-request."""

    id: uuid.UUID
    firm_id: uuid.UUID
    email: str
    role: str
    is_active: bool


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    """FastAPI dependency: decode JWT, validate user, return CurrentUser.

    Raises HTTP 401 if the token is missing, expired, or malformed.
    Raises HTTP 403 if the account is inactive.
    """
    try:
        payload = decode_access_token(token)
        user_id = uuid.UUID(payload["sub"])
        firm_id = uuid.UUID(payload["firm_id"])
        role = payload.get("role", "VIEWER")
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise _CREDENTIALS_EXCEPTION from None

    user = await UserRepository.get_by_id(db, user_id)
    if user is None:
        raise _CREDENTIALS_EXCEPTION

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    # Sanity-check: the firm_id in the token must match the DB record.
    # This guards against stale tokens issued before a user was moved.
    if user.firm_id != firm_id or user.role != role:
        raise _CREDENTIALS_EXCEPTION

    return CurrentUser(
        id=user.id,
        firm_id=user.firm_id,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
    )


def require_admin(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Dependency to ensure the current user is an Admin."""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return current_user


def require_lawyer(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Dependency to ensure the current user is an Admin or Lawyer."""
    if current_user.role not in ("ADMIN", "LAWYER"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Lawyer access required.",
        )
    return current_user
