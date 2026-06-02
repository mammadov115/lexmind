#!/bin/bash

# Configuration
BASE_URL="http://localhost:8000"

echo "=== 1. Checking API Health ==="
curl -i -X GET "${BASE_URL}/health" \
  -H "Content-Type: application/json"
echo -e "\n\n"

echo "=== 2. Registering Law Firm (Success Case) ==="
curl -i -X POST "${BASE_URL}/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Apex Legal Group",
    "admin_user": {
      "email": "admin@apexlegal.com",
      "password": "SecurePassword123"
    }
  }'
echo -e "\n\n"

echo "=== 3. Registering Law Firm (Duplicate Email Case - Expect HTTP 400) ==="
curl -i -X POST "${BASE_URL}/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Different Legal Group",
    "admin_user": {
      "email": "admin@apexlegal.com",
      "password": "SecurePassword123"
    }
  }'
echo -e "\n\n"

echo "=== 4. Registering Law Firm (Duplicate Name Case - Expect HTTP 400) ==="
curl -i -X POST "${BASE_URL}/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Apex Legal Group",
    "admin_user": {
      "email": "anotheradmin@apexlegal.com",
      "password": "SecurePassword123"
    }
  }'
echo -e "\n\n"

echo "=== 5. Registering Law Firm (Weak Password Case - Expect HTTP 422) ==="
curl -i -X POST "${BASE_URL}/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Weak Pass Legal",
    "admin_user": {
      "email": "admin@weakpass.com",
      "password": "short"
    }
  }'
echo -e "\n"
