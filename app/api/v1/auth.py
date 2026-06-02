from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas import FirmRegisterRequest, FirmRegisterResponse
from app.schemas.auth import TokenResponse
from app.services.auth import LoginService, RegistrationService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=FirmRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new Law Firm and Admin User",
    description=(
        "Registers a new law firm with a unique name/slug "
        "and creates its primary administrator user."
    ),
)
async def register(
    request: FirmRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> FirmRegisterResponse:
    """Endpoint to handle Law Firm and Admin User registration."""
    firm, admin_user = await RegistrationService.register_law_firm(db, request)
    return FirmRegisterResponse(firm=firm, admin_user=admin_user)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login and obtain a JWT access token",
    description=(
        "Accepts email (as `username`) and `password` via form data. "
        "Returns a signed Bearer token with `firm_id` embedded."
    ),
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Validate credentials and issue a JWT with firm_id claim."""
    token = await LoginService.login(
        db,
        email=form_data.username,
        password=form_data.password,
    )
    return TokenResponse(access_token=token)
