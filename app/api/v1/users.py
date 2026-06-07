import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import (
    CurrentUser,
    get_current_user,
    require_admin,
    require_lawyer,
)
from app.repositories.user import TenantUserRepository
from app.schemas.user import (
    UserChangePassword,
    UserResponse,
    UserUpdateProfile,
)
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user",
)
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Return the profile of the currently authenticated user."""
    repo = TenantUserRepository(db, current_user.firm_id)
    user = await repo.get_by_id(current_user.id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return UserResponse.model_validate(user)


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user's profile",
)
async def update_me(
    update_data: UserUpdateProfile,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Update profile information for the currently authenticated user."""
    repo = TenantUserRepository(db, current_user.firm_id)
    user = await repo.get_by_id(current_user.id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    updated_user = await UserService.update_profile(db, user, update_data)
    return UserResponse.model_validate(updated_user)


@router.put(
    "/me/password",
    status_code=status.HTTP_200_OK,
    summary="Change user password",
)
async def change_password(
    password_data: UserChangePassword,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Change the password for the currently authenticated user.

    Requires the current password to be verified.
    Invalidates all previously issued tokens.
    """
    repo = TenantUserRepository(db, current_user.firm_id)
    user = await repo.get_by_id(current_user.id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    await UserService.change_password(db, user, password_data)
    return {"message": "Password changed successfully."}


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get a specific user within the authenticated firm",
)
async def get_user(
    user_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Return a user by ID, scoped to the current tenant's firm_id.

    Returns 404 if the user does not exist OR belongs to another firm.
    This is the primary cross-tenant isolation enforcement point.
    """
    repo = TenantUserRepository(db, current_user.firm_id)
    user = await repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return UserResponse.model_validate(user)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Invite a new user to the firm (Admin only)",
)
async def invite_user(
    current_user: CurrentUser = Depends(require_admin),
) -> dict[str, str]:
    """Invite a new user. Only ADMINs can perform this action."""
    return {"message": "User invited successfully."}


@router.post(
    "/lawyer-only",
    status_code=status.HTTP_200_OK,
    summary="A dummy endpoint for Lawyer/Admin only",
)
async def lawyer_action(
    current_user: CurrentUser = Depends(require_lawyer),
) -> dict[str, str]:
    """Perform a lawyer action. Only LAWYERs and ADMINs can perform this."""
    return {"message": "Lawyer action successful."}
