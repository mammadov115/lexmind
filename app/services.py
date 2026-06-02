from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import EmailAlreadyExistsError, FirmNameAlreadyExistsError
from app.models import Firm, User
from app.schemas import FirmRegisterRequest
from app.utils import hash_password, slugify_name


async def _generate_unique_slug(db: AsyncSession, name: str) -> str:
    """Generate a unique slug for the law firm, appending a suffix if conflicts exist."""
    base_slug = slugify_name(name)
    slug = base_slug
    counter = 1
    while True:
        stmt = select(Firm).where(Firm.slug == slug)
        result = await db.execute(stmt)
        if not result.scalar_one_or_none():
            break
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


class RegistrationService:
    """Service class for handling registration logic."""

    @staticmethod
    async def register_law_firm(
        db: AsyncSession,
        request: FirmRegisterRequest,
    ) -> tuple[Firm, User]:
        """Atomically register a new Law Firm and its initial Admin User.

        If either operation fails, database is rolled back.
        """
        try:
            # Validate uniqueness of Email
            email_stmt = select(User).where(User.email == request.admin_user.email)
            email_res = await db.execute(email_stmt)
            if email_res.scalar_one_or_none():
                raise EmailAlreadyExistsError(request.admin_user.email)

            # Validate uniqueness of Firm Name
            firm_stmt = select(Firm).where(Firm.name == request.name)
            firm_res = await db.execute(firm_stmt)
            if firm_res.scalar_one_or_none():
                raise FirmNameAlreadyExistsError(request.name)

            # Generate slug
            slug = await _generate_unique_slug(db, request.name)

            # Create the Firm
            db_firm = Firm(
                name=request.name,
                slug=slug,
            )
            db.add(db_firm)
            await db.flush()  # Populates db_firm.id

            # Hash password and create Admin User
            hashed_pw = hash_password(request.admin_user.password)
            db_user = User(
                email=request.admin_user.email,
                hashed_password=hashed_pw,
                is_active=True,
                is_admin=True,
                firm_id=db_firm.id,
            )
            db.add(db_user)
            await db.flush()

            # Commit the transaction
            await db.commit()

        except Exception:
            await db.rollback()
            raise

        # Refresh objects to load generated relationships/IDs post-commit
        await db.refresh(db_firm)
        await db.refresh(db_user)

        return db_firm, db_user
