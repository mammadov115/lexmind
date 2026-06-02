"""
TASK-02: Cross-tenant isolation tests.

Acceptance criteria: a user authenticated under Firm A's token must be
completely unable to read, access, or enumerate data belonging to Firm B.
"""

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Login tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, firm_a: dict) -> None:
    """Successful login returns a Bearer token."""
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "alpha@firm.com", "password": "SecurePassword123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, firm_a: dict) -> None:
    """Wrong password returns HTTP 401."""
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "alpha@firm.com", "password": "WrongPassword999"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client: AsyncClient) -> None:
    """Unknown email returns HTTP 401."""
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "ghost@nowhere.com", "password": "Whatever123"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Protected endpoint — unauthenticated access
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_me_without_token(client: AsyncClient) -> None:
    """Accessing /users/me without a token returns HTTP 401."""
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_with_invalid_token(client: AsyncClient) -> None:
    """Accessing /users/me with a forged token returns HTTP 401."""
    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer totally.fake.token"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# /users/me — own-firm access
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_me_returns_own_user(
    client: AsyncClient, firm_a: dict, token_a: str
) -> None:
    """Authenticated user can retrieve their own profile."""
    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "alpha@firm.com"
    assert body["firm_id"] == firm_a["firm"]["id"]
    assert "hashed_password" not in body


# ---------------------------------------------------------------------------
# CORE: Cross-tenant isolation tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cross_tenant_user_isolation(
    client: AsyncClient,
    firm_a: dict,
    firm_b: dict,
    token_a: str,
    token_b: str,
) -> None:
    """Firm A's token CANNOT access Firm B's user by user_id.

    The TenantUserRepository scopes the query to firm_id from the JWT.
    Even with a valid user_id from Firm B, the query returns nothing
    and the endpoint responds with 404.
    """
    firm_b_user_id = firm_b["admin_user"]["id"]

    # Firm A token tries to fetch Firm B's user directly by UUID
    resp = await client.get(
        f"/api/v1/users/{firm_b_user_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    # Must be 404 — not 200, not 403.
    # 404 is intentional: we reveal no information about whether the
    # user exists at all in the system.
    assert resp.status_code == 404, (
        f"Expected 404 but got {resp.status_code}. "
        "Cross-tenant isolation is BROKEN."
    )


@pytest.mark.asyncio
async def test_cross_tenant_reverse_isolation(
    client: AsyncClient,
    firm_a: dict,
    firm_b: dict,
    token_a: str,
    token_b: str,
) -> None:
    """Firm B's token CANNOT access Firm A's user — isolation is symmetric."""
    firm_a_user_id = firm_a["admin_user"]["id"]

    resp = await client.get(
        f"/api/v1/users/{firm_a_user_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 404, (
        f"Expected 404 but got {resp.status_code}. "
        "Cross-tenant isolation is BROKEN."
    )


@pytest.mark.asyncio
async def test_own_firm_user_is_accessible(
    client: AsyncClient,
    firm_a: dict,
    token_a: str,
) -> None:
    """Firm A's token CAN access its own user by user_id (positive case)."""
    firm_a_user_id = firm_a["admin_user"]["id"]

    resp = await client.get(
        f"/api/v1/users/{firm_a_user_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == firm_a_user_id


@pytest.mark.asyncio
async def test_firm_id_in_token_matches_user_firm(
    client: AsyncClient,
    firm_a: dict,
    firm_b: dict,
    token_a: str,
) -> None:
    """The firm_id in the JWT is correctly bound to the registering firm."""
    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 200
    # The firm_id on the profile must match Firm A — never Firm B
    assert resp.json()["firm_id"] == firm_a["firm"]["id"]
    assert resp.json()["firm_id"] != firm_b["firm"]["id"]
