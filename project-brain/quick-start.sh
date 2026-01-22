#!/bin/bash

set -e

echo "??????????????????????????????????????????????????????????????"
echo "?        Project Brain - Quick Start Setup Script           ?"
echo "??????????????????????????????????????????????????????????????"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check dependencies
echo -e "${BLUE}Checking dependencies...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}? Docker is not installed${NC}"
    echo "Download from: https://www.docker.com/products/docker-desktop"
    exit 1
fi
echo -e "${GREEN}? Docker found${NC}"

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}? Docker Compose is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}? Docker Compose found${NC}"

echo ""
echo -e "${BLUE}Starting services...${NC}"

# Start services
docker-compose up -d

echo ""
echo -e "${BLUE}Waiting for services to be healthy...${NC}"
sleep 15

# Check if services are running
if docker-compose ps | grep -q "postgres.*Up"; then
    echo -e "${GREEN}? PostgreSQL is running${NC}"
else
    echo -e "${RED}? PostgreSQL failed to start${NC}"
    docker-compose logs postgres
    exit 1
fi

if docker-compose ps | grep -q "redis.*Up"; then
    echo -e "${GREEN}? Redis is running${NC}"
else
    echo -e "${RED}? Redis failed to start${NC}"
    exit 1
fi

if docker-compose ps | grep -q "qdrant.*Up"; then
    echo -e "${GREEN}? Qdrant is running${NC}"
else
    echo -e "${RED}? Qdrant failed to start${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Running database migrations...${NC}"
docker-compose exec -T backend python -m alembic upgrade head
echo -e "${GREEN}? Migrations completed${NC}"

echo ""
echo -e "${BLUE}Seeding database with demo data...${NC}"
docker-compose exec -T backend python seed_data.py
echo -e "${GREEN}? Database seeded${NC}"

echo ""
echo "??????????????????????????????????????????????????????????????"
echo -e "?          ${GREEN}? Setup Complete!${NC}                              ?"
echo "??????????????????????????????????????????????????????????????"
echo ""
echo "Services are now running:"
echo ""
echo -e "  ${BLUE}Frontend:${NC}        http://localhost:3000"
echo -e "  ${BLUE}API:${NC}             http://localhost:8000"
echo -e "  ${BLUE}API Docs:${NC}        http://localhost:8000/docs"
echo -e "  ${BLUE}Qdrant UI:${NC}       http://localhost:6333/dashboard"
echo -e "  ${BLUE}MinIO:${NC}           http://localhost:9001 (admin/admin)"
echo -e "  ${BLUE}Neo4j:${NC}           http://localhost:7474 (neo4j/neo4j_password)"
echo ""
echo "Useful commands:"
echo ""
echo -e "  ${BLUE}View logs:${NC}"
echo "    docker-compose logs -f backend"
echo "    docker-compose logs -f worker"
echo "    docker-compose logs -f ui"
echo ""
echo -e "  ${BLUE}Stop services:${NC}"
echo "    docker-compose down"
echo ""
echo -e "  ${BLUE}Database shell:${NC}"
echo "    docker-compose exec postgres psql -U brain_user -d project_brain"
echo ""
echo -e "  ${BLUE}Run tests:${NC}"
echo "    curl http://localhost:8000/health"
echo ""
echo "?? Full documentation: See README.md"
echo ""
