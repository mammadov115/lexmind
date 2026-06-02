from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import FirmRegisterRequest, FirmRegisterResponse
from app.services import RegistrationService

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
