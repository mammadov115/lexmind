from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, slugify_name
from app.exceptions import EmailAlreadyExistsError, FirmNameAlreadyExistsError
from app.models.firm import Firm
from app.models.user import User
from app.repositories.firm import FirmRepository
from app.repositories.user import UserRepository
from app.schemas.firm import FirmRegisterRequest


async def _generate_unique_slug(db: AsyncSession, name: str) -> str:
    """Generate a unique slug for the law firm.

    Appends a suffix if conflicts exist.
    """
    base_slug = slugify_name(name)
    slug = base_slug
    counter = 1
    while True:
        if not await FirmRepository.get_by_slug(db, slug):
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
            # Validate uniqueness of Email using Repository
            if await UserRepository.get_by_email(db, request.admin_user.email):
                raise EmailAlreadyExistsError(request.admin_user.email)

            # Validate uniqueness of Firm Name using Repository
            if await FirmRepository.get_by_name(db, request.name):
                raise FirmNameAlreadyExistsError(request.name)

            # Generate slug
            slug = await _generate_unique_slug(db, request.name)

            # Create the Firm using Repository
            db_firm = await FirmRepository.create(
                db, name=request.name, slug=slug
            )

            # Hash password and create Admin User using Repository
            hashed_pw = hash_password(request.admin_user.password)
            db_user = await UserRepository.create(
                db,
                email=request.admin_user.email,
                hashed_password=hashed_pw,
                is_active=True,
                is_admin=True,
                firm_id=db_firm.id,
            )

            # Commit the transaction
            await db.commit()

        except Exception:
            await db.rollback()
            raise

        # Refresh objects to load generated relationships/IDs post-commit
        await db.refresh(db_firm)
        await db.refresh(db_user)

        return db_firm, db_user
