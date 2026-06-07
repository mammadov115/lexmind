from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, utc_now, verify_password
from app.exceptions import EmailAlreadyExistsError, InvalidCredentialsError
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserChangePassword, UserUpdateProfile


class UserService:
    """Service class for managing user accounts."""

    @staticmethod
    async def update_profile(
        db: AsyncSession,
        user: User,
        update_data: UserUpdateProfile,
    ) -> User:
        """Update a user's profile information.

        Raises EmailAlreadyExistsError if the new email is already taken.
        """
        if update_data.email and update_data.email != user.email:
            existing = await UserRepository.get_by_email(db, update_data.email)
            if existing:
                raise EmailAlreadyExistsError(update_data.email)
            user.email = update_data.email

        if update_data.first_name is not None:
            user.first_name = update_data.first_name
        if update_data.last_name is not None:
            user.last_name = update_data.last_name

        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def change_password(
        db: AsyncSession,
        user: User,
        password_data: UserChangePassword,
    ) -> User:
        """Change a user's password.

        Verifies the current password and validates the new one.
        Updates the `password_changed_at` timestamp.
        """
        if not verify_password(
            password_data.current_password, user.hashed_password
        ):
            raise InvalidCredentialsError()

        user.hashed_password = hash_password(password_data.new_password)
        user.password_changed_at = utc_now()

        await db.commit()
        await db.refresh(user)
        return user
