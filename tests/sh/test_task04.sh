#!/bin/bash

# =============================================================================
# TASK-04 Manual Test: Auth, Password, Account Management
# Run the server first: make run
# Then execute: ./tests/sh/test_task04.sh
# =============================================================================

BASE_URL="http://localhost:8000"
REGISTER_URL="${BASE_URL}/api/v1/auth/register"
LOGIN_URL="${BASE_URL}/api/v1/auth/login"
REFRESH_URL="${BASE_URL}/api/v1/auth/refresh"
ME_URL="${BASE_URL}/api/v1/users/me"
PASSWORD_URL="${BASE_URL}/api/v1/users/me/password"

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

UID_STR=$(date +%s)
EMAIL="user_${UID_STR}@task04.com"
OLD_PW="SecurePassword123"
NEW_PW="NewSecurePassword123"

# =============================================================================
# STEP 1: Registration and Login
# =============================================================================
section "1. Registration & Login"

# Register
curl -s -X POST "${REGISTER_URL}" -H "Content-Type: application/json" \
  -d '{"name": "Firm '"${UID_STR}"'", "admin_user": {"email": "'"${EMAIL}"'", "password": "'"${OLD_PW}"'"}}' > /dev/null

# Login
LOGIN_RESP=$(curl -s -X POST "${LOGIN_URL}" -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${EMAIL}&password=${OLD_PW}")

ACCESS_TOKEN=$(echo "${LOGIN_RESP}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token', ''))")
REFRESH_TOKEN=$(echo "${LOGIN_RESP}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('refresh_token', ''))")

if [ -n "${ACCESS_TOKEN}" ] && [ -n "${REFRESH_TOKEN}" ]; then
  pass "Login successful, got access and refresh tokens."
else
  fail "Failed to login or missing tokens."
  exit 1
fi


# =============================================================================
# STEP 2: Refresh Token
# =============================================================================
section "2. Refresh Token"

REFRESH_RESP=$(curl -s -X POST "${REFRESH_URL}" -H "Content-Type: application/json" \
  -d '{"refresh_token": "'"${REFRESH_TOKEN}"'"}')

NEW_ACCESS_TOKEN=$(echo "${REFRESH_RESP}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token', ''))")

if [ -n "${NEW_ACCESS_TOKEN}" ]; then
  pass "Refresh successful, got new access token."
else
  fail "Failed to refresh token."
fi


# =============================================================================
# STEP 3: Profile Management
# =============================================================================
section "3. Get & Update Profile"

# Get Profile
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET "${ME_URL}" -H "Authorization: Bearer ${ACCESS_TOKEN}")
if [ "${STATUS}" = "200" ]; then pass "Get current profile returned 200"; else fail "Expected 200, got ${STATUS}"; fi

# Update Profile
UPDATE_RESP=$(curl -s -X PUT "${ME_URL}" -H "Authorization: Bearer ${ACCESS_TOKEN}" -H "Content-Type: application/json" \
  -d '{"first_name": "John", "last_name": "Doe"}')
FIRST_NAME=$(echo "${UPDATE_RESP}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('first_name', ''))")

if [ "${FIRST_NAME}" = "John" ]; then
  pass "Profile updated successfully (first_name = John)."
else
  fail "Failed to update profile."
fi


# =============================================================================
# STEP 4: Change Password & Token Invalidation
# =============================================================================
section "4. Change Password & Security Verification"

# Store the old token to verify it gets invalidated
OLD_ACCESS_TOKEN="${ACCESS_TOKEN}"

# Change Password
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X PUT "${PASSWORD_URL}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" -H "Content-Type: application/json" \
  -d '{"current_password": "'"${OLD_PW}"'", "new_password": "'"${NEW_PW}"'"}')

if [ "${STATUS}" = "200" ]; then pass "Password changed successfully."; else fail "Expected 200 on password change, got ${STATUS}"; fi

# Verify old password fails
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${LOGIN_URL}" -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${EMAIL}&password=${OLD_PW}")
if [ "${STATUS}" = "401" ]; then pass "Old password correctly rejected (401)."; else fail "Expected 401 with old password, got ${STATUS}"; fi

# Verify new password works
LOGIN_RESP_NEW=$(curl -s -X POST "${LOGIN_URL}" -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${EMAIL}&password=${NEW_PW}")
NEW_LOGIN_TOKEN=$(echo "${LOGIN_RESP_NEW}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token', ''))")

if [ -n "${NEW_LOGIN_TOKEN}" ]; then pass "Login successful with new password."; else fail "Login failed with new password."; fi

# Verify old token is INVALIDATED
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET "${ME_URL}" -H "Authorization: Bearer ${OLD_ACCESS_TOKEN}")
if [ "${STATUS}" = "401" ]; then pass "Previously issued token is now INVALID (401)."; else fail "SECURITY FLAW! Old token still valid (Got ${STATUS})."; fi

# Verify new token works
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET "${ME_URL}" -H "Authorization: Bearer ${NEW_LOGIN_TOKEN}")
if [ "${STATUS}" = "200" ]; then pass "New token correctly allowed (200)."; else fail "New token rejected."; fi


# =============================================================================
# Summary
# =============================================================================

echo -e "\n${BOLD}${YELLOW}=== Manual Task 04 Test Complete ===${RESET}"
echo
