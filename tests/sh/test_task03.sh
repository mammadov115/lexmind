#!/bin/bash

# =============================================================================
# TASK-03 Manual Test: Role-Based Access Control (RBAC)
# Run the server first: make run
# Then execute: ./tests/sh/test_task03.sh
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

# Generate a unique prefix to avoid email conflicts on rerun
UID_STR=$(date +%s)

# =============================================================================
# STEP 1: Register Users and Setup Roles
# =============================================================================

section "1. Setting up Users and Roles"

# 1. ADMIN
echo "Registering Admin..."
curl -s -X POST "${REGISTER_URL}" -H "Content-Type: application/json" \
  -d '{"name": "Admin Firm '"${UID_STR}"'", "admin_user": {"email": "admin_'"${UID_STR}"'@task03.com", "password": "SecurePassword123"}}' > /dev/null

TOKEN_ADMIN=$(curl -s -X POST "${LOGIN_URL}" -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin_${UID_STR}@task03.com&password=SecurePassword123" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
pass "Admin user created and token obtained."

# 2. LAWYER
echo "Registering Lawyer..."
curl -s -X POST "${REGISTER_URL}" -H "Content-Type: application/json" \
  -d '{"name": "Lawyer Firm '"${UID_STR}"'", "admin_user": {"email": "lawyer_'"${UID_STR}"'@task03.com", "password": "SecurePassword123"}}' > /dev/null

# Downgrade role to LAWYER in DB directly for testing
python3 -c "import sqlite3; conn = sqlite3.connect('lexmind.db'); conn.execute(\"UPDATE users SET role='LAWYER' WHERE email='lawyer_${UID_STR}@task03.com'\"); conn.commit(); conn.close()"

TOKEN_LAWYER=$(curl -s -X POST "${LOGIN_URL}" -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=lawyer_${UID_STR}@task03.com&password=SecurePassword123" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
pass "Lawyer user created, role updated in DB, and token obtained."

# 3. VIEWER
echo "Registering Viewer..."
curl -s -X POST "${REGISTER_URL}" -H "Content-Type: application/json" \
  -d '{"name": "Viewer Firm '"${UID_STR}"'", "admin_user": {"email": "viewer_'"${UID_STR}"'@task03.com", "password": "SecurePassword123"}}' > /dev/null

# Downgrade role to VIEWER in DB directly for testing
python3 -c "import sqlite3; conn = sqlite3.connect('lexmind.db'); conn.execute(\"UPDATE users SET role='VIEWER' WHERE email='viewer_${UID_STR}@task03.com'\"); conn.commit(); conn.close()"

TOKEN_VIEWER=$(curl -s -X POST "${LOGIN_URL}" -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=viewer_${UID_STR}@task03.com&password=SecurePassword123" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
pass "Viewer user created, role updated in DB, and token obtained."

# =============================================================================
# STEP 2: Test Admin Endpoint (POST /api/v1/users) -> Only Admin
# =============================================================================

section "2. Test Admin Endpoint (Invite User) - Requires ADMIN"

# ADMIN
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/api/v1/users" -H "Authorization: Bearer ${TOKEN_ADMIN}")
if [ "${STATUS}" = "201" ]; then pass "Admin got 201 (Allowed)"; else fail "Admin expected 201, got ${STATUS}"; fi

# LAWYER
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/api/v1/users" -H "Authorization: Bearer ${TOKEN_LAWYER}")
if [ "${STATUS}" = "403" ]; then pass "Lawyer got 403 (Blocked)"; else fail "Lawyer expected 403, got ${STATUS}"; fi

# VIEWER
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/api/v1/users" -H "Authorization: Bearer ${TOKEN_VIEWER}")
if [ "${STATUS}" = "403" ]; then pass "Viewer got 403 (Blocked)"; else fail "Viewer expected 403, got ${STATUS}"; fi


# =============================================================================
# STEP 3: Test Lawyer Endpoint (POST /api/v1/users/lawyer-only) -> Admin/Lawyer
# =============================================================================

section "3. Test Lawyer Endpoint - Requires ADMIN or LAWYER"

# ADMIN
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/api/v1/users/lawyer-only" -H "Authorization: Bearer ${TOKEN_ADMIN}")
if [ "${STATUS}" = "200" ]; then pass "Admin got 200 (Allowed)"; else fail "Admin expected 200, got ${STATUS}"; fi

# LAWYER
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/api/v1/users/lawyer-only" -H "Authorization: Bearer ${TOKEN_LAWYER}")
if [ "${STATUS}" = "200" ]; then pass "Lawyer got 200 (Allowed)"; else fail "Lawyer expected 200, got ${STATUS}"; fi

# VIEWER
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/api/v1/users/lawyer-only" -H "Authorization: Bearer ${TOKEN_VIEWER}")
if [ "${STATUS}" = "403" ]; then pass "Viewer got 403 (Blocked)"; else fail "Viewer expected 403, got ${STATUS}"; fi


# =============================================================================
# STEP 4: Test Viewer Endpoint (GET /api/v1/users/me) -> Any Authenticated User
# =============================================================================

section "4. Test Viewer Endpoint (/users/me) - Requires Authenticated User"

# ADMIN
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET "${BASE_URL}/api/v1/users/me" -H "Authorization: Bearer ${TOKEN_ADMIN}")
if [ "${STATUS}" = "200" ]; then pass "Admin got 200 (Allowed)"; else fail "Admin expected 200, got ${STATUS}"; fi

# LAWYER
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET "${BASE_URL}/api/v1/users/me" -H "Authorization: Bearer ${TOKEN_LAWYER}")
if [ "${STATUS}" = "200" ]; then pass "Lawyer got 200 (Allowed)"; else fail "Lawyer expected 200, got ${STATUS}"; fi

# VIEWER
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET "${BASE_URL}/api/v1/users/me" -H "Authorization: Bearer ${TOKEN_VIEWER}")
if [ "${STATUS}" = "200" ]; then pass "Viewer got 200 (Allowed)"; else fail "Viewer expected 200, got ${STATUS}"; fi


# =============================================================================
# Summary
# =============================================================================

echo -e "\n${BOLD}${YELLOW}=== Manual RBAC Test Complete ===${RESET}"
echo -e "You can run ${CYAN}make test${RESET} for the automated version."
echo
