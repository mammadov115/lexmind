import asyncio
import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.database import get_db
from app.main import app
from app.models import Base

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test engine and create all database tables."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated database session for each test."""
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with session_factory() as session:
        yield session
        # Ensure we roll back transactions after every test to keep
        # tests isolated.
        await session.rollback()


@pytest.fixture
async def client(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """Provide an AsyncClient with dependency overrides for testing."""

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers for multi-tenant tests
# ---------------------------------------------------------------------------

_REGISTER_URL = "/api/v1/auth/register"
_LOGIN_URL = "/api/v1/auth/login"


async def register_firm(client: AsyncClient, name: str, email: str) -> dict:
    """Register a firm and return the parsed response body."""
    resp = await client.post(
        _REGISTER_URL,
        json={
            "name": name,
            "admin_user": {"email": email, "password": "SecurePassword123"},
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def login(client: AsyncClient, email: str) -> str:
    """Login and return the raw access token string."""
    resp = await client.post(
        _LOGIN_URL,
        data={"username": email, "password": "SecurePassword123"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture
async def firm_a(client: AsyncClient) -> dict:
    """Registered Firm A with admin user."""
    uid = uuid.uuid4().hex[:6]
    return await register_firm(
        client, f"Firm Alpha {uid}", f"alpha_{uid}@firm.com"
    )


@pytest.fixture
async def firm_b(client: AsyncClient) -> dict:
    """Registered Firm B with admin user."""
    uid = uuid.uuid4().hex[:6]
    return await register_firm(
        client, f"Firm Beta {uid}", f"beta_{uid}@firm.com"
    )


@pytest.fixture
async def token_a(client: AsyncClient, firm_a: dict) -> str:
    """JWT token for Firm A admin."""
    return await login(client, firm_a["admin_user"]["email"])


@pytest.fixture
async def token_b(client: AsyncClient, firm_b: dict) -> str:
    """JWT token for Firm B admin."""
    return await login(client, firm_b["admin_user"]["email"])
