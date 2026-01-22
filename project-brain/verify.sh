#!/bin/bash

# Project Brain - Verification Script
# Run this after quick-start to verify everything is working

set -e

echo ""
echo "?????????????????????????????????????????????????????????????????"
echo "?  Project Brain - Post-Deployment Verification Script         ?"
echo "?????????????????????????????????????????????????????????????????"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASSED=0
FAILED=0

# Function to test and report
test_endpoint() {
    local name=$1
    local url=$2
    local method=${3:-"GET"}
    
    echo -n "Testing ${name}... "
    
    if [ "$method" == "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$url" \
            -H "Content-Type: application/json" \
            -d '{}' 2>/dev/null | tail -1)
    else
        response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null | tail -1)
    fi
    
    if [ "$response" = "200" ] || [ "$response" = "201" ]; then
        echo -e "${GREEN}?${NC}"
        ((PASSED++))
    else
        echo -e "${RED}?${NC} (HTTP $response)"
        ((FAILED++))
    fi
}

# Function to test container status
test_container() {
    local name=$1
    
    echo -n "Checking ${name}... "
    if docker-compose ps "$name" | grep -q "Up"; then
        echo -e "${GREEN}?${NC}"
        ((PASSED++))
    else
        echo -e "${RED}?${NC}"
        ((FAILED++))
    fi
}

echo -e "${BLUE}1. Checking Docker Services${NC}"
echo "================================================"
test_container "postgres"
test_container "redis"
test_container "qdrant"
test_container "minio"
test_container "backend"
test_container "worker"
test_container "ui"
echo ""

echo -e "${BLUE}2. Testing API Endpoints${NC}"
echo "================================================"
test_endpoint "Health Check" "http://localhost:8000/health"
test_endpoint "Documents List" "http://localhost:8000/documents"
test_endpoint "Lexicon List" "http://localhost:8000/lexicon"
test_endpoint "Projects List" "http://localhost:8000/entities/projects"
echo ""

echo -e "${BLUE}3. Testing Frontend${NC}"
echo "================================================"
echo -n "Frontend accessible... "
response=$(curl -s -w "\n%{http_code}" "http://localhost:3000" 2>/dev/null | tail -1)
if [ "$response" = "200" ]; then
    echo -e "${GREEN}?${NC}"
    ((PASSED++))
else
    echo -e "${RED}?${NC}"
    ((FAILED++))
fi
echo ""

echo -e "${BLUE}4. Testing Database${NC}"
echo "================================================"
echo -n "Database connection... "
if docker-compose exec -T postgres psql -U brain_user -d project_brain -c "SELECT COUNT(*) FROM documents;" >/dev/null 2>&1; then
    echo -e "${GREEN}?${NC}"
    ((PASSED++))
else
    echo -e "${RED}?${NC}"
    ((FAILED++))
fi

echo -n "Database tables... "
count=$(docker-compose exec -T postgres psql -U brain_user -d project_brain -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | grep -o "[0-9]*" | tail -1)
if [ "$count" -ge 10 ]; then
    echo -e "${GREEN}?${NC} ($count tables)"
    ((PASSED++))
else
    echo -e "${RED}?${NC}"
    ((FAILED++))
fi
echo ""

echo -e "${BLUE}5. Testing Storage${NC}"
echo "================================================"
echo -n "MinIO connection... "
if curl -s http://localhost:9000/minio/health/live >/dev/null 2>&1; then
    echo -e "${GREEN}?${NC}"
    ((PASSED++))
else
    echo -e "${RED}?${NC}"
    ((FAILED++))
fi

echo -n "Qdrant connection... "
if curl -s http://localhost:6333/health >/dev/null 2>&1; then
    echo -e "${GREEN}?${NC}"
    ((PASSED++))
else
    echo -e "${RED}?${NC}"
    ((FAILED++))
fi
echo ""

echo -e "${BLUE}6. Service URLs${NC}"
echo "================================================"
echo -e "Frontend:        ${BLUE}http://localhost:3000${NC}"
echo -e "API:             ${BLUE}http://localhost:8000${NC}"
echo -e "API Docs:        ${BLUE}http://localhost:8000/docs${NC}"
echo -e "Qdrant UI:       ${BLUE}http://localhost:6333/dashboard${NC}"
echo -e "MinIO Console:   ${BLUE}http://localhost:9001${NC} (admin/admin)"
echo -e "Neo4j Browser:   ${BLUE}http://localhost:7474${NC}"
echo ""

echo -e "${BLUE}7. Summary${NC}"
echo "================================================"
echo -e "Tests Passed:  ${GREEN}$PASSED${NC}"
echo -e "Tests Failed:  ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}? All tests passed! Project Brain is ready to use.${NC}"
    echo ""
    echo "?? Next steps:"
    echo "  1. Open http://localhost:3000 in your browser"
    echo "  2. Go to Documents page"
    echo "  3. Upload a PDF, DOCX, or TXT file"
    echo "  4. Watch it parse and extract automatically"
    echo "  5. Try searching at http://localhost:3000/search"
    echo ""
    echo "?? Documentation:"
    echo "  - README.md: Setup and API reference"
    echo "  - ARCHITECTURE.md: Technical deep-dive"
    echo "  - http://localhost:8000/docs: Interactive API docs"
    echo ""
else
    echo -e "${YELLOW}? Some tests failed. Troubleshooting:${NC}"
    echo ""
    echo "Common issues:"
    echo "  • Services not fully started: wait 30 seconds and retry"
    echo "  • Port conflicts: check if ports 3000, 8000, 5432, 6379, 6333, 9000 are free"
    echo "  • Docker daemon not running: start Docker Desktop or daemon"
    echo ""
    echo "View logs:"
    echo "  docker-compose logs backend"
    echo "  docker-compose logs worker"
    echo "  docker-compose logs postgres"
    echo ""
    exit 1
fi
