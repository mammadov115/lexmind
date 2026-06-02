from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Response schema returned after a successful login."""

    access_token: str
    token_type: str = "bearer"
