@echo off
REM Project Brain - Quick Start Setup Script (Windows)

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo        Project Brain - Quick Start Setup Script
echo ============================================================
echo.

REM Check for Docker
echo Checking for Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not installed or not in PATH
    echo Download from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo OK: Docker found

REM Check for Docker Compose
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker Compose is not installed
    pause
    exit /b 1
)
echo OK: Docker Compose found

echo.
echo Starting services...
docker-compose up -d

echo.
echo Waiting for services to be healthy (15 seconds)...
timeout /t 15 /nobreak

echo.
echo Checking services...
docker-compose ps | find "postgres" >nul
if %errorlevel% neq 0 (
    echo ERROR: PostgreSQL failed to start
    docker-compose logs postgres
    pause
    exit /b 1
)
echo OK: PostgreSQL is running

docker-compose ps | find "redis" >nul
if %errorlevel% neq 0 (
    echo ERROR: Redis failed to start
    pause
    exit /b 1
)
echo OK: Redis is running

docker-compose ps | find "qdrant" >nul
if %errorlevel% neq 0 (
    echo ERROR: Qdrant failed to start
    pause
    exit /b 1
)
echo OK: Qdrant is running

echo.
echo Running database migrations...
docker-compose exec -T backend python -m alembic upgrade head
echo OK: Migrations completed

echo.
echo Seeding database with demo data...
docker-compose exec -T backend python seed_data.py
echo OK: Database seeded

echo.
echo ============================================================
echo              SETUP COMPLETE!
echo ============================================================
echo.
echo Services are now running:
echo.
echo   Frontend:        http://localhost:3000
echo   API:             http://localhost:8000
echo   API Docs:        http://localhost:8000/docs
echo   Qdrant UI:       http://localhost:6333/dashboard
echo   MinIO:           http://localhost:9001 (admin/admin)
echo   Neo4j:           http://localhost:7474 (neo4j/neo4j_password)
echo.
echo Useful commands:
echo.
echo   View backend logs:
echo     docker-compose logs -f backend
echo.
echo   View worker logs:
echo     docker-compose logs -f worker
echo.
echo   Stop services:
echo     docker-compose down
echo.
echo   Database shell:
echo     docker-compose exec postgres psql -U brain_user -d project_brain
echo.
echo See README.md for full documentation.
echo.
pause
