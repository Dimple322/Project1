.PHONY: help up down logs build rebuild clean migrate seed test lint format

help:
	@echo "Project Brain - Development Commands"
	@echo "====================================="
	@echo ""
	@echo "Make targets:"
	@echo "  make up              - Start all services"
	@echo "  make down            - Stop all services"
	@echo "  make rebuild         - Rebuild all containers"
	@echo "  make logs            - Show logs from all services"
	@echo "  make logs-backend    - Show backend logs only"
	@echo "  make logs-worker     - Show worker logs only"
	@echo "  make logs-ui         - Show UI logs only"
	@echo "  make migrate         - Run database migrations"
	@echo "  make seed            - Seed database with demo data"
	@echo "  make clean           - Remove all containers and volumes"
	@echo "  make test-api        - Test API health"
	@echo "  make format-python   - Format Python code with black"
	@echo "  make lint-python     - Lint Python code"
	@echo "  make format-frontend - Format frontend code with prettier"
	@echo "  make shell-backend   - Open shell in backend container"
	@echo "  make shell-db        - Open psql shell"
	@echo ""
	@echo "Services:"
	@echo "  Frontend: http://localhost:3000"
	@echo "  API: http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo "  Qdrant: http://localhost:6333/dashboard"
	@echo "  MinIO: http://localhost:9001 (admin/admin)"
	@echo "  Neo4j: http://localhost:7474 (neo4j/neo4j_password)"

up:
	@echo "Starting all services..."
	docker-compose up -d
	@echo "Waiting for services to be healthy..."
	sleep 10
	@echo "Services started! Check http://localhost:3000"

down:
	@echo "Stopping all services..."
	docker-compose down

rebuild:
	@echo "Rebuilding containers..."
	docker-compose down
	docker-compose up -d --build
	@echo "Services rebuilt!"

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-worker:
	docker-compose logs -f worker

logs-ui:
	docker-compose logs -f ui

build:
	docker-compose build

migrate:
	@echo "Running database migrations..."
	docker-compose exec backend python -m alembic upgrade head
	@echo "Migrations complete!"

seed:
	@echo "Seeding database with demo data..."
	docker-compose exec backend python seed_data.py
	@echo "Database seeded!"

clean:
	@echo "Removing all containers and volumes..."
	docker-compose down -v
	@echo "Cleaned up!"

test-api:
	@echo "Testing API health..."
	@curl -s http://localhost:8000/health | python -m json.tool
	@echo ""

test-search:
	@echo "Testing search endpoint..."
	@curl -s -X POST http://localhost:8000/search \
		-H "Content-Type: application/json" \
		-d '{"query": "test", "limit": 5}' | python -m json.tool

test-documents:
	@echo "Testing documents list..."
	@curl -s http://localhost:8000/documents | python -m json.tool

shell-backend:
	docker-compose exec backend bash

shell-db:
	docker-compose exec postgres psql -U brain_user -d project_brain

format-python:
	@echo "Formatting Python code..."
	docker-compose exec backend black --line-length 100 .
	@echo "Done!"

lint-python:
	@echo "Linting Python code..."
	docker-compose exec backend flake8 . --max-line-length=100
	@echo "Done!"

format-frontend:
	@echo "Formatting frontend code..."
	cd ui && npx prettier --write . --ignore-path .gitignore
	@echo "Done!"

init: up migrate seed
	@echo "Project initialized!"
	@echo "Frontend: http://localhost:3000"
	@echo "API: http://localhost:8000/docs"

dev-backend:
	cd backend && python -m venv venv
	. backend/venv/bin/activate
	pip install -r backend/requirements.txt
	@echo "Run: python backend/main.py"

dev-frontend:
	cd ui && npm install
	@echo "Run: npm run dev"

ps:
	docker-compose ps

stats:
	docker stats

prune:
	@echo "Pruning Docker system..."
	docker system prune -a --volumes -f
	@echo "Done!"
