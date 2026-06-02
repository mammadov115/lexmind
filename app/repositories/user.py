import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import TenantRepository


class UserRepository:
    """Unscoped repository for auth-only operations (login, token lookup).

    These methods are intentionally global — they are used only during
    authentication before a firm_id is known.
    """

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> User | None:
        """Retrieve a user by their email address (unscoped)."""
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
        """Retrieve a user by UUID (unscoped — used by JWT dependency)."""
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        email: str,
        hashed_password: str,
        is_active: bool = True,
        role: str = "VIEWER",
        firm_id: uuid.UUID,
    ) -> User:
        """Create a new user in database."""
        db_user = User(
            email=email,
            hashed_password=hashed_password,
            is_active=is_active,
            role=role,
            firm_id=firm_id,
        )
        db.add(db_user)
        await db.flush()
        return db_user


class TenantUserRepository(TenantRepository):
    """Tenant-scoped repository for User queries within a single firm.

    All queries are automatically filtered by ``firm_id``.
    Instantiate with a valid firm_id — never use this without one.
    """

    model = User

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Retrieve a user by UUID, scoped to the current tenant."""
        stmt = self._scope(select(User)).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> list[User]:
        """List all users belonging to the current tenant."""
        stmt = self._scope(select(User))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
