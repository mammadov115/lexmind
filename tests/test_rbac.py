"""
TASK-03: Role-Based Access Control (RBAC) tests.

Acceptance criteria:
- Admin can access everything.
- Lawyer can access lawyer endpoints and viewer endpoints.
- Viewer can only access viewer endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import User


@pytest.fixture
def create_test_token(firm_a, db_session: AsyncSession):
    """Helper to create a custom token with a specific role."""

    async def _create(role: str) -> str:
        import uuid

        # Update the user's role in the DB to match the token
        user_id = uuid.UUID(firm_a["admin_user"]["id"])
        stmt = update(User).where(User.id == user_id).values(role=role)
        await db_session.execute(stmt)
        await db_session.commit()

        return create_access_token(
            subject=user_id,
            firm_id=firm_a["firm"]["id"],
            role=role,
        )

    return _create


@pytest.mark.asyncio
async def test_admin_can_access_admin_endpoints(
    client: AsyncClient, create_test_token
) -> None:
    token = await create_test_token("ADMIN")

    # Can access Admin endpoint
    resp = await client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201

    # Can access Lawyer endpoint
    resp = await client.post(
        "/api/v1/users/lawyer-only",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    # Can access Viewer endpoint
    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_lawyer_cannot_access_admin_endpoints(
    client: AsyncClient, create_test_token
) -> None:
    token = await create_test_token("LAWYER")

    # CANNOT access Admin endpoint
    resp = await client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403

    # Can access Lawyer endpoint
    resp = await client.post(
        "/api/v1/users/lawyer-only",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_viewer_cannot_access_lawyer_endpoints(
    client: AsyncClient, create_test_token
) -> None:
    token = await create_test_token("VIEWER")

    # CANNOT access Admin endpoint
    resp = await client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403

    # CANNOT access Lawyer endpoint
    resp = await client.post(
        "/api/v1/users/lawyer-only",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403

    # Can access Viewer endpoint
    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
