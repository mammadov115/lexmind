import re
import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRole(StrEnum):
    """Enumeration of available user roles."""

    ADMIN = "ADMIN"
    LAWYER = "LAWYER"
    VIEWER = "VIEWER"


class UserRegister(BaseModel):
    """Schema for validating user registration data."""

    email: EmailStr
    password: str = Field(
        ...,
        description=(
            "Password must be at least 8 characters long, contain at least "
            "one uppercase letter, one lowercase letter, and one digit."
        ),
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        """Validate that the password meets security requirements."""
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[a-z]", value):
            raise ValueError(
                "Password must contain at least one lowercase letter."
            )
        if not re.search(r"[A-Z]", value):
            raise ValueError(
                "Password must contain at least one uppercase letter."
            )
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit.")
        return value


class UserResponse(BaseModel):
    """Schema for returning user details."""

    id: uuid.UUID
    email: EmailStr
    is_active: bool
    role: UserRole
    firm_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }
