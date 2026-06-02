#!/bin/bash

# =============================================================================
# TASK-02 Manual Test: Multi-Tenant Isolation
# Run the server first: make run
# Then execute: ./tests/test_task02.sh
# =============================================================================

BASE_URL="http://localhost:8000"
REGISTER_URL="${BASE_URL}/api/v1/auth/register"
LOGIN_URL="${BASE_URL}/api/v1/auth/login"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

pass() { echo -e "  ${GREEN}✓ PASS${RESET} — $1"; }
fail() { echo -e "  ${RED}✗ FAIL${RESET} — $1"; }
section() { echo -e "\n${BOLD}${CYAN}=== $1 ===${RESET}"; }

# =============================================================================
# STEP 1: Register two separate firms
# =============================================================================

section "1. Registering Firm A (alpha@alpha.com)"
FIRM_A_RESP=$(curl -s -X POST "${REGISTER_URL}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Task02 Firm Alpha",
    "admin_user": {
      "email": "alpha@task02.com",
      "password": "SecurePassword123"
    }
  }')
echo "  Response: ${FIRM_A_RESP}" | head -c 300
echo

FIRM_A_ID=$(echo "${FIRM_A_RESP}" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
FIRM_A_USER_ID=$(echo "${FIRM_A_RESP}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['admin_user']['id'])")
echo "  Firm A user ID: ${FIRM_A_USER_ID}"

section "2. Registering Firm B (beta@beta.com)"
FIRM_B_RESP=$(curl -s -X POST "${REGISTER_URL}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Task02 Firm Beta",
    "admin_user": {
      "email": "beta@task02.com",
      "password": "SecurePassword123"
    }
  }')
echo "  Response: ${FIRM_B_RESP}" | head -c 300
echo

FIRM_B_USER_ID=$(echo "${FIRM_B_RESP}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['admin_user']['id'])")
echo "  Firm B user ID: ${FIRM_B_USER_ID}"

# =============================================================================
# STEP 2: Login and capture tokens
# =============================================================================

section "3. Login as Firm A"
TOKEN_A_RESP=$(curl -s -X POST "${LOGIN_URL}" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alpha@task02.com&password=SecurePassword123")
TOKEN_A=$(echo "${TOKEN_A_RESP}" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
if [ -n "${TOKEN_A}" ]; then
  pass "Firm A token obtained"
  echo "  Token (first 60 chars): ${TOKEN_A:0:60}..."
else
  fail "Could not obtain Firm A token"
fi

section "4. Login as Firm B"
TOKEN_B_RESP=$(curl -s -X POST "${LOGIN_URL}" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=beta@task02.com&password=SecurePassword123")
TOKEN_B=$(echo "${TOKEN_B_RESP}" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
if [ -n "${TOKEN_B}" ]; then
  pass "Firm B token obtained"
  echo "  Token (first 60 chars): ${TOKEN_B:0:60}..."
else
  fail "Could not obtain Firm B token"
fi

# =============================================================================
# STEP 3: Auth guard tests
# =============================================================================

section "5. Access /users/me WITHOUT token (expect 401)"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET "${BASE_URL}/api/v1/users/me")
if [ "${STATUS}" = "401" ]; then
  pass "Got 401 as expected"
else
  fail "Expected 401, got ${STATUS}"
fi

section "6. Access /users/me with FORGED token (expect 401)"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET "${BASE_URL}/api/v1/users/me" \
  -H "Authorization: Bearer totally.fake.jwt.token")
if [ "${STATUS}" = "401" ]; then
  pass "Got 401 as expected"
else
  fail "Expected 401, got ${STATUS}"
fi

section "7. Login with WRONG password (expect 401)"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${LOGIN_URL}" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alpha@task02.com&password=WrongPassword999")
if [ "${STATUS}" = "401" ]; then
  pass "Got 401 as expected"
else
  fail "Expected 401, got ${STATUS}"
fi

# =============================================================================
# STEP 4: Own-firm access (positive cases)
# =============================================================================

section "8. Firm A reads /users/me with its own token (expect 200)"
RESP=$(curl -s -X GET "${BASE_URL}/api/v1/users/me" \
  -H "Authorization: Bearer ${TOKEN_A}")
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET "${BASE_URL}/api/v1/users/me" \
  -H "Authorization: Bearer ${TOKEN_A}")
if [ "${STATUS}" = "200" ]; then
  pass "Firm A can read its own profile"
  echo "  Email: $(echo "${RESP}" | python3 -c "import sys,json; print(json.load(sys.stdin)['email'])")"
else
  fail "Expected 200, got ${STATUS}"
fi

section "9. Firm A reads its own user by ID (expect 200)"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET \
  "${BASE_URL}/api/v1/users/${FIRM_A_USER_ID}" \
  -H "Authorization: Bearer ${TOKEN_A}")
if [ "${STATUS}" = "200" ]; then
  pass "Firm A can read its own user by ID"
else
  fail "Expected 200, got ${STATUS}"
fi

section "10. Firm B reads its own user by ID (expect 200)"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET \
  "${BASE_URL}/api/v1/users/${FIRM_B_USER_ID}" \
  -H "Authorization: Bearer ${TOKEN_B}")
if [ "${STATUS}" = "200" ]; then
  pass "Firm B can read its own user by ID"
else
  fail "Expected 200, got ${STATUS}"
fi

# =============================================================================
# STEP 5: CORE — Cross-tenant isolation (must all return 404)
# =============================================================================

section "11. [ISOLATION] Firm A token reads Firm B user by ID (expect 404)"
RESP=$(curl -s -X GET "${BASE_URL}/api/v1/users/${FIRM_B_USER_ID}" \
  -H "Authorization: Bearer ${TOKEN_A}")
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET \
  "${BASE_URL}/api/v1/users/${FIRM_B_USER_ID}" \
  -H "Authorization: Bearer ${TOKEN_A}")
if [ "${STATUS}" = "404" ]; then
  pass "Firm A CANNOT access Firm B user — isolation holds"
else
  fail "ISOLATION BROKEN: Expected 404, got ${STATUS}. Response: ${RESP}"
fi

section "12. [ISOLATION] Firm B token reads Firm A user by ID (expect 404)"
RESP=$(curl -s -X GET "${BASE_URL}/api/v1/users/${FIRM_A_USER_ID}" \
  -H "Authorization: Bearer ${TOKEN_B}")
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET \
  "${BASE_URL}/api/v1/users/${FIRM_A_USER_ID}" \
  -H "Authorization: Bearer ${TOKEN_B}")
if [ "${STATUS}" = "404" ]; then
  pass "Firm B CANNOT access Firm A user — isolation holds"
else
  fail "ISOLATION BROKEN: Expected 404, got ${STATUS}. Response: ${RESP}"
fi

# =============================================================================
# Summary
# =============================================================================

echo -e "\n${BOLD}${YELLOW}=== Manual Test Complete ===${RESET}"
echo -e "Run ${CYAN}make test${RESET} to execute the full automated suite."
echo
