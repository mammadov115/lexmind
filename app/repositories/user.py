import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Repository for managing database operations on User models."""

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> User | None:
        """Retrieve a user by their email address."""
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        email: str,
        hashed_password: str,
        is_active: bool = True,
        is_admin: bool = False,
        firm_id: uuid.UUID,
    ) -> User:
        """Create a new user in database."""
        db_user = User(
            email=email,
            hashed_password=hashed_password,
            is_active=is_active,
            is_admin=is_admin,
            firm_id=firm_id,
        )
        db.add(db_user)
        await db.flush()
        return db_user
