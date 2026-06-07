import uuid
from datetime import datetime, timedelta

import bcrypt
import jwt
from slugify import slugify

from app.core.config import settings
from app.models.base import utc_now

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def hash_password(password: str) -> str:
    """Generate a bcrypt hash of the plain password."""
    pw_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pw_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hashed value."""
    pw_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    try:
        return bcrypt.checkpw(pw_bytes, hashed_bytes)
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Slug helpers
# ---------------------------------------------------------------------------


def slugify_name(name: str) -> str:
    """Convert a name into a URL-friendly, lowercased slug."""
    return slugify(name)


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def create_access_token(
    subject: uuid.UUID,
    firm_id: uuid.UUID,
    role: str,
    pwd_at: datetime | None = None,
) -> str:
    """Encode a signed JWT with sub, firm_id, role, and pwd_at."""
    expire = utc_now() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(subject),
        "firm_id": str(firm_id),
        "role": role,
        "iat": int(utc_now().timestamp()),
        "exp": expire,
    }
    if pwd_at:
        payload["pwd_at"] = int(pwd_at.timestamp())

    return jwt.encode(
        payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )


def create_refresh_token(
    subject: uuid.UUID,
    firm_id: uuid.UUID,
    role: str,
    pwd_at: datetime | None = None,
) -> str:
    """Encode a signed JWT refresh token."""
    expire = utc_now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": str(subject),
        "firm_id": str(firm_id),
        "role": role,
        "type": "refresh",
        "iat": int(utc_now().timestamp()),
        "exp": expire,
    }
    if pwd_at:
        payload["pwd_at"] = int(pwd_at.timestamp())

    return jwt.encode(
        payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )


def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT; raises jwt.InvalidTokenError on failure."""
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
