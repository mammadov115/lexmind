from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.firm import Firm


class FirmRepository:
    """Repository for managing database operations on Firm models."""

    @staticmethod
    async def get_by_name(db: AsyncSession, name: str) -> Firm | None:
        """Retrieve a firm by its name."""
        stmt = select(Firm).where(Firm.name == name)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_slug(db: AsyncSession, slug: str) -> Firm | None:
        """Retrieve a firm by its slug."""
        stmt = select(Firm).where(Firm.slug == slug)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, *, name: str, slug: str) -> Firm:
        """Create a new firm in database."""
        db_firm = Firm(name=name, slug=slug)
        db.add(db_firm)
        await db.flush()  # Populate generated fields like id, created_at, etc.
        return db_firm
