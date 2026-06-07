import uuid

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    slugify_name,
    verify_password,
)
from app.exceptions import (
    EmailAlreadyExistsError,
    FirmNameAlreadyExistsError,
    InvalidCredentialsError,
)
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
            if await UserRepository.get_by_email(db, request.admin_user.email):
                raise EmailAlreadyExistsError(request.admin_user.email)

            if await FirmRepository.get_by_name(db, request.name):
                raise FirmNameAlreadyExistsError(request.name)

            slug = await _generate_unique_slug(db, request.name)

            db_firm = await FirmRepository.create(
                db, name=request.name, slug=slug
            )

            hashed_pw = hash_password(request.admin_user.password)
            db_user = await UserRepository.create(
                db,
                email=request.admin_user.email,
                hashed_password=hashed_pw,
                is_active=True,
                role="ADMIN",
                firm_id=db_firm.id,
            )

            await db.commit()

        except Exception:
            await db.rollback()
            raise

        await db.refresh(db_firm)
        await db.refresh(db_user)

        return db_firm, db_user


class LoginService:
    """Service class for handling user login and token issuance."""

    @staticmethod
    async def login(
        db: AsyncSession,
        email: str,
        password: str,
    ) -> tuple[str, str]:
        """Validate credentials and return signed access and refresh tokens.

        Raises InvalidCredentialsError if email or password is wrong.
        """
        user = await UserRepository.get_by_email(db, email)
        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()

        access_token = create_access_token(
            subject=user.id,
            firm_id=user.firm_id,
            role=user.role,
            pwd_at=user.password_changed_at,
        )
        refresh_token = create_refresh_token(
            subject=user.id,
            firm_id=user.firm_id,
            role=user.role,
            pwd_at=user.password_changed_at,
        )
        return access_token, refresh_token

    @staticmethod
    async def refresh_token(
        db: AsyncSession,
        token: str,
    ) -> tuple[str, str]:
        """Issue new tokens given a valid refresh token."""
        try:
            payload = decode_access_token(token)
            if payload.get("type") != "refresh":
                raise InvalidCredentialsError()
            user_id = uuid.UUID(payload["sub"])
            pwd_at = payload.get("pwd_at")
        except (jwt.InvalidTokenError, KeyError, ValueError) as e:
            raise InvalidCredentialsError() from e

        user = await UserRepository.get_by_id(db, user_id)
        if user is None or not user.is_active:
            raise InvalidCredentialsError()

        if user.password_changed_at:
            pw_ts = int(user.password_changed_at.timestamp())
            if not pwd_at or pwd_at < pw_ts:
                raise InvalidCredentialsError()

        access_token = create_access_token(
            subject=user.id,
            firm_id=user.firm_id,
            role=user.role,
            pwd_at=user.password_changed_at,
        )
        new_refresh_token = create_refresh_token(
            subject=user.id,
            firm_id=user.firm_id,
            role=user.role,
            pwd_at=user.password_changed_at,
        )
        return access_token, new_refresh_token
