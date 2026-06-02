from unittest.mock import patch
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Firm, User
from app.schemas import FirmRegisterRequest
from app.services import RegistrationService


@pytest.mark.asyncio
async def test_register_firm_success(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test successful registration of a Law Firm and its Admin User."""
    payload = {
        "name": "Acme Law Chambers",
        "admin_user": {
            "email": "admin@acmelaw.com",
            "password": "SecurePassword123",
        },
    }

    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert "firm" in data
    assert "admin_user" in data

    # Verify firm details
    firm_data = data["firm"]
    assert firm_data["name"] == "Acme Law Chambers"
    assert firm_data["slug"] == "acme-law-chambers"
    assert "id" in firm_data

    # Verify user details
    user_data = data["admin_user"]
    assert user_data["email"] == "admin@acmelaw.com"
    assert user_data["is_admin"] is True
    assert user_data["is_active"] is True
    assert "id" in user_data
    assert "hashed_password" not in user_data
    assert "password" not in user_data

    # Verify database persistence
    firm_stmt = select(Firm).where(Firm.name == "Acme Law Chambers")
    firm_res = await db_session.execute(firm_stmt)
    db_firm = firm_res.scalar_one_or_none()
    assert db_firm is not None
    assert db_firm.slug == "acme-law-chambers"

    user_stmt = select(User).where(User.email == "admin@acmelaw.com")
    user_res = await db_session.execute(user_stmt)
    db_user = user_res.scalar_one_or_none()
    assert db_user is not None
    assert db_user.firm_id == db_firm.id


@pytest.mark.asyncio
async def test_register_firm_duplicate_email(client: AsyncClient) -> None:
    """Test registration fails when the email is already registered."""
    payload1 = {
        "name": "First Law Firm",
        "admin_user": {
            "email": "shared@law.com",
            "password": "SecurePassword123",
        },
    }
    response1 = await client.post("/api/v1/auth/register", json=payload1)
    assert response1.status_code == 201

    payload2 = {
        "name": "Second Law Firm",
        "admin_user": {
            "email": "shared@law.com",
            "password": "AnotherPassword456",
        },
    }
    response2 = await client.post("/api/v1/auth/register", json=payload2)
    assert response2.status_code == 400
    assert response2.json()["detail"] == "Email 'shared@law.com' is already registered."


@pytest.mark.asyncio
async def test_register_firm_duplicate_name(client: AsyncClient) -> None:
    """Test registration fails when the firm name is already registered."""
    payload1 = {
        "name": "Unique Law",
        "admin_user": {
            "email": "user1@uniquelaw.com",
            "password": "SecurePassword123",
        },
    }
    response1 = await client.post("/api/v1/auth/register", json=payload1)
    assert response1.status_code == 201

    payload2 = {
        "name": "Unique Law",
        "admin_user": {
            "email": "user2@uniquelaw.com",
            "password": "SecurePassword123",
        },
    }
    response2 = await client.post("/api/v1/auth/register", json=payload2)
    assert response2.status_code == 400
    assert response2.json()["detail"] == "Firm name 'Unique Law' is already registered."


@pytest.mark.asyncio
async def test_register_firm_slug_collision(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test unique slug generation when name is similar but not identical (bypassing name uniqueness).

    e.g., "Apex Law" vs "Apex Law!" which both map to slug "apex-law".
    """
    payload1 = {
        "name": "Apex Law",
        "admin_user": {
            "email": "user1@apex.com",
            "password": "SecurePassword123",
        },
    }
    response1 = await client.post("/api/v1/auth/register", json=payload1)
    assert response1.status_code == 201
    assert response1.json()["firm"]["slug"] == "apex-law"

    # "Apex Law!" will not trigger the unique name check because the names differ.
    # But it will generate a conflicting slug "apex-law".
    payload2 = {
        "name": "Apex Law!",
        "admin_user": {
            "email": "user2@apex.com",
            "password": "SecurePassword123",
        },
    }
    response2 = await client.post("/api/v1/auth/register", json=payload2)
    assert response2.status_code == 201
    assert response2.json()["firm"]["slug"] == "apex-law-1"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "password,error_msg",
    [
        ("short", "Password must be at least 8 characters long"),
        ("nouppercase123", "Password must contain at least one uppercase letter"),
        ("NOLOWERCASE123", "Password must contain at least one lowercase letter"),
        ("NoDigitsHere", "Password must contain at least one digit"),
    ],
)
async def test_register_invalid_password(client: AsyncClient, password: str, error_msg: str) -> None:
    """Test password strength validation rules in the Pydantic schema."""
    payload = {
        "name": "Invalid Pass Firm",
        "admin_user": {
            "email": "test@invalidpass.com",
            "password": password,
        },
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(error_msg in err["msg"] for err in errors)


@pytest.mark.asyncio
async def test_registration_transaction_rollback(db_session: AsyncSession) -> None:
    """Test that if user creation fails, the firm creation is rolled back (atomic transaction)."""
    request_data = FirmRegisterRequest(
        name="Rollback Firm",
        admin_user={
            "email": "rollback@example.com",
            "password": "SecurePassword123",
        },
    )

    # Mock hash_password to raise an exception, failing user registration midway
    with patch("app.services.hash_password", side_effect=ValueError("Simulated hashing failure")):
        with pytest.raises(ValueError, match="Simulated hashing failure"):
            await RegistrationService.register_law_firm(db_session, request_data)

    # Check that "Rollback Firm" was NOT created in the database
    stmt = select(Firm).where(Firm.name == "Rollback Firm")
    res = await db_session.execute(stmt)
    firm = res.scalar_one_or_none()
    assert firm is None, "Firm should not have been created due to transaction rollback."
