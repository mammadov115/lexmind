import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.user import UserRegister, UserResponse


class FirmRegisterRequest(BaseModel):
    """Schema for registering a new Law Firm and its Admin User."""

    name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="The unique name of the law firm.",
    )
    admin_user: UserRegister


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
