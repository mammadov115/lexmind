"""
TASK-02: Cross-tenant isolation tests.

Acceptance criteria: a user authenticated under Firm A's token must be
completely unable to read, access, or enumerate data belonging to Firm B.
"""

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_REGISTER_URL = "/api/v1/auth/register"
_LOGIN_URL = "/api/v1/auth/login"
_ME_URL = "/api/v1/users/me"


async def _register(client: AsyncClient, name: str, email: str) -> dict:
    resp = await client.post(
        _REGISTER_URL,
        json={
            "name": name,
            "admin_user": {
                "email": email,
                "password": "SecurePassword123",
            },
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _login(client: AsyncClient, email: str) -> str:
    resp = await client.post(
        _LOGIN_URL,
        data={"username": email, "password": "SecurePassword123"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Login tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    """Successful login returns a Bearer token."""
    await _register(client, "Login Firm", "login@firm.com")
    resp = await client.post(
        _LOGIN_URL,
        data={"username": "login@firm.com", "password": "SecurePassword123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    """Wrong password returns HTTP 401."""
    await _register(client, "WrongPw Firm", "wrongpw@firm.com")
    resp = await client.post(
        _LOGIN_URL,
        data={"username": "wrongpw@firm.com", "password": "NotTheRight1"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client: AsyncClient) -> None:
    """Unknown email returns HTTP 401."""
    resp = await client.post(
        _LOGIN_URL,
        data={"username": "ghost@nowhere.com", "password": "Whatever123"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Protected endpoint — unauthenticated access
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_me_without_token(client: AsyncClient) -> None:
    """Accessing /users/me without a token returns HTTP 401."""
    resp = await client.get(_ME_URL)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_with_invalid_token(client: AsyncClient) -> None:
    """Accessing /users/me with a forged token returns HTTP 401."""
    resp = await client.get(
        _ME_URL,
        headers={"Authorization": "Bearer totally.fake.token"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# /users/me — own-firm access
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_me_returns_own_user(client: AsyncClient) -> None:
    """Authenticated user can retrieve their own profile."""
    firm = await _register(client, "Me Firm", "me@firm.com")
    token = await _login(client, "me@firm.com")

    resp = await client.get(_ME_URL, headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "me@firm.com"
    assert body["firm_id"] == firm["firm"]["id"]
    assert "hashed_password" not in body


# ---------------------------------------------------------------------------
# CORE: Cross-tenant isolation tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cross_tenant_user_isolation(client: AsyncClient) -> None:
    """Firm A's token CANNOT access Firm B's user by user_id.

    The TenantUserRepository scopes the query to firm_id from the JWT.
    Even with a valid user_id from Firm B, the query returns nothing
    and the endpoint responds with 404.
    """
    _firm_a = await _register(
        client, "Isol Firm Alpha", "isol_alpha@alpha.com"
    )
    firm_b = await _register(client, "Isol Firm Beta", "isol_beta@beta.com")
    token_a = await _login(client, "isol_alpha@alpha.com")

    firm_b_user_id = firm_b["admin_user"]["id"]

    # Firm A token tries to fetch Firm B's user directly by UUID
    resp = await client.get(
        f"/api/v1/users/{firm_b_user_id}",
        headers=_auth(token_a),
    )
    # Must be 404, not 200 or 403.
    # We reveal no information about whether the user exists at all.
    assert resp.status_code == 404, (
        f"Expected 404 but got {resp.status_code}. "
        "Cross-tenant isolation is BROKEN."
    )


@pytest.mark.asyncio
async def test_cross_tenant_reverse_isolation(client: AsyncClient) -> None:
    """Firm B's token CANNOT access Firm A's user — isolation is symmetric."""
    firm_a = await _register(client, "Alpha Reverse", "alpha@reverse.com")
    _firm_b = await _register(client, "Beta Reverse", "beta@reverse.com")
    token_b = await _login(client, "beta@reverse.com")

    firm_a_user_id = firm_a["admin_user"]["id"]

    resp = await client.get(
        f"/api/v1/users/{firm_a_user_id}",
        headers=_auth(token_b),
    )
    assert resp.status_code == 404, (
        f"Expected 404 but got {resp.status_code}. "
        "Cross-tenant isolation is BROKEN."
    )


@pytest.mark.asyncio
async def test_own_firm_user_is_accessible(client: AsyncClient) -> None:
    """Firm A's token CAN access its own user by user_id (positive case)."""
    firm_a = await _register(client, "Positive Firm", "positive@firm.com")
    token_a = await _login(client, "positive@firm.com")

    firm_a_user_id = firm_a["admin_user"]["id"]

    resp = await client.get(
        f"/api/v1/users/{firm_a_user_id}",
        headers=_auth(token_a),
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == firm_a_user_id


@pytest.mark.asyncio
async def test_firm_id_in_token_matches_user_firm(
    client: AsyncClient,
) -> None:
    """The firm_id in the JWT is correctly bound to the registering firm."""
    firm_a = await _register(client, "Bound Firm A", "bound_a@firm.com")
    firm_b = await _register(client, "Bound Firm B", "bound_b@firm.com")
    token_a = await _login(client, "bound_a@firm.com")

    resp = await client.get(_ME_URL, headers=_auth(token_a))
    assert resp.status_code == 200
    body = resp.json()
    # firm_id on the profile must match Firm A — never Firm B
    assert body["firm_id"] == firm_a["firm"]["id"]
    assert body["firm_id"] != firm_b["firm"]["id"]
