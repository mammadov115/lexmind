import re
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


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


class FirmRegisterRequest(BaseModel):
    """Schema for registering a new Law Firm and its Admin User."""

    name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="The unique name of the law firm.",
    )
    admin_user: UserRegister


class UserResponse(BaseModel):
    """Schema for returning user details."""

    id: uuid.UUID
    email: EmailStr
    is_active: bool
    is_admin: bool
    firm_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class FirmResponse(BaseModel):
    """Schema for returning law firm details."""

    id: uuid.UUID
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class FirmRegisterResponse(BaseModel):
    """Schema for the registration endpoint response."""

    firm: FirmResponse
    admin_user: UserResponse

    model_config = {
        "from_attributes": True,
    }
