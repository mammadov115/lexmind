from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Response schema returned after a successful login."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshRequest(BaseModel):
    """Request schema to obtain a new access token using a refresh token."""

    refresh_token: str
