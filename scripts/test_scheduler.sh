#!/bin/bash

# Script to test scheduler endpoints
# Usage: ./scripts/test_scheduler.sh [local|production] [CRON_SECRET]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENV=${1:-local}
CRON_SECRET=${2:-"test-secret-for-local-dev"}

if [ "$ENV" = "local" ]; then
    BASE_URL="http://localhost:8000"
    echo -e "${YELLOW}Testing LOCAL environment${NC}"
elif [ "$ENV" = "production" ]; then
    BASE_URL="https://encheres-backend.onrender.com"
    echo -e "${YELLOW}Testing PRODUCTION environment${NC}"

    if [ "$CRON_SECRET" = "test-secret-for-local-dev" ]; then
        echo -e "${RED}ERROR: You must provide the production CRON_SECRET${NC}"
        echo "Usage: $0 production YOUR_CRON_SECRET"
        exit 1
    fi
else
    echo -e "${RED}ERROR: Invalid environment. Use 'local' or 'production'${NC}"
    exit 1
fi

echo "Base URL: $BASE_URL"
echo ""

# Test 1: Health check
echo -e "${YELLOW}[1/5] Testing health endpoint...${NC}"
response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health")
if [ "$response" -eq 200 ]; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${RED}✗ Health check failed (HTTP $response)${NC}"
fi
echo ""

# Test 2: Jobs status (no auth required)
echo -e "${YELLOW}[2/5] Testing jobs status endpoint...${NC}"
response=$(curl -s "$BASE_URL/api/v1/scheduler/jobs-status")
echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
echo ""

# Test 3: Scraping endpoint without secret (should fail)
echo -e "${YELLOW}[3/5] Testing scraping endpoint without secret (should fail)...${NC}"
response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/scheduler/trigger-scraping")
http_code=$(echo "$response" | tail -n1)
if [ "$http_code" -eq 401 ]; then
    echo -e "${GREEN}✓ Correctly rejected (HTTP 401)${NC}"
else
    echo -e "${RED}✗ Unexpected response (HTTP $http_code)${NC}"
fi
echo ""

# Test 4: Scraping endpoint with valid secret
echo -e "${YELLOW}[4/5] Testing scraping endpoint with valid secret...${NC}"
response=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "X-Cron-Secret: $CRON_SECRET" \
    "$BASE_URL/api/v1/scheduler/trigger-scraping")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" -eq 200 ]; then
    echo -e "${GREEN}✓ Scraping job triggered successfully${NC}"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo -e "${RED}✗ Scraping job failed (HTTP $http_code)${NC}"
    echo "$body"
fi
echo ""

# Test 5: Discovery endpoint with valid secret
echo -e "${YELLOW}[5/5] Testing discovery endpoint with valid secret...${NC}"
response=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "X-Cron-Secret: $CRON_SECRET" \
    "$BASE_URL/api/v1/scheduler/trigger-discovery")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" -eq 200 ]; then
    echo -e "${GREEN}✓ Discovery job triggered successfully${NC}"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo -e "${RED}✗ Discovery job failed (HTTP $http_code)${NC}"
    echo "$body"
fi
echo ""

echo -e "${GREEN}Testing complete!${NC}"
