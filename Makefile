# ==============================================================================
# RAG Fortress - Docker Management Makefile
# ==============================================================================
# Convenience commands for managing Docker deployments
# Usage: make [command]
# ==============================================================================

.PHONY: help build up down restart logs clean backup db-backup db-restore health

# Colors for terminal output
BLUE := \033[0;34m
GREEN := \033[0;32m
RED := \033[0;31m
NC := \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

## help: Display this help message
help:
	@echo "$(BLUE)RAG Fortress - Docker Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Setup:$(NC)"
	@echo "  make setup          - Initial setup (copy env files)"
	@echo "  make build          - Build all Docker images"
	@echo "  make build-backend  - Build backend image only"
	@echo "  make build-frontend - Build frontend image only"
	@echo ""
	@echo "$(GREEN)Deployment:$(NC)"
	@echo "  make up             - Start all services (detached)"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make dev            - Start in development mode (with logs)"
	@echo "  make backend-dev    - Start backend only"
	@echo "  make frontend-dev   - Start frontend only"
	@echo ""
	@echo "$(GREEN)Monitoring:$(NC)"
	@echo "  make logs           - View all logs (follow)"
	@echo "  make logs-backend   - View backend logs"
	@echo "  make logs-frontend  - View frontend logs"
	@echo "  make health         - Check health of all services"
	@echo "  make ps             - Show running containers"
	@echo ""
	@echo "$(GREEN)Database:$(NC)"
	@echo "  make db-migrate     - Run database migrations"
	@echo "  make db-backup      - Backup PostgreSQL database"
	@echo "  make db-restore     - Restore PostgreSQL database"
	@echo "  make db-shell       - Open PostgreSQL shell"
	@echo ""
	@echo "$(GREEN)Maintenance:$(NC)"
	@echo "  make clean          - Stop and remove containers"
	@echo "  make clean-volumes  - Remove all volumes (DANGER!)"
	@echo "  make prune          - Remove unused Docker resources"
	@echo "  make update         - Pull latest images and rebuild"
	@echo ""

## setup: Initial setup - copy environment files
setup:
	@echo "$(BLUE)Setting up environment files...$(NC)"
	@test -f .env || (cp .env.docker.example .env && echo "$(GREEN)Created .env$(NC)")
	@test -f backend/.env || (cp backend/.env.example backend/.env && echo "$(GREEN)Created backend/.env$(NC)")
	@echo "$(GREEN)Setup complete! Edit .env files with your configuration.$(NC)"

## build: Build all Docker images
build:
	@echo "$(BLUE)Building all images...$(NC)"
	docker compose build --no-cache

## build-backend: Build backend image only
build-backend:
	@echo "$(BLUE)Building backend image...$(NC)"
	docker compose build --no-cache backend

## build-frontend: Build frontend image only
build-frontend:
	@echo "$(BLUE)Building frontend image...$(NC)"
	docker compose build --no-cache frontend

## up: Start all services in detached mode
up:
	@echo "$(BLUE)Starting services...$(NC)"
	docker compose up -d
	@echo "$(GREEN)Services started!$(NC)"
	@make health

## down: Stop all services
down:
	@echo "$(BLUE)Stopping services...$(NC)"
	docker compose down
	@echo "$(GREEN)Services stopped!$(NC)"

## restart: Restart all services
restart:
	@echo "$(BLUE)Restarting services...$(NC)"
	docker compose restart
	@echo "$(GREEN)Services restarted!$(NC)"

## dev: Start services in development mode (with logs)
dev:
	@echo "$(BLUE)Starting in development mode...$(NC)"
	docker compose up

## backend-dev: Start backend services only
backend-dev:
	@echo "$(BLUE)Starting backend in development mode...$(NC)"
	cd backend && docker compose up

## frontend-dev: Start frontend service only
frontend-dev:
	@echo "$(BLUE)Starting frontend in development mode...$(NC)"
	cd frontend && docker compose up

## logs: View logs for all services
logs:
	docker compose logs -f

## logs-backend: View backend logs
logs-backend:
	docker compose logs -f backend

## logs-frontend: View frontend logs
logs-frontend:
	docker compose logs -f frontend

## logs-db: View database logs
logs-db:
	docker compose logs -f postgres

## health: Check health status of all services
health:
	@echo "$(BLUE)Checking service health...$(NC)"
	@docker compose ps
	@echo ""
	@echo "$(BLUE)Health checks:$(NC)"
	@docker compose exec -T backend curl -sf http://localhost:8000/health > /dev/null && echo "$(GREEN)✓ Backend healthy$(NC)" || echo "$(RED)✗ Backend unhealthy$(NC)"
	@docker compose exec -T frontend curl -sf http://localhost:3000/health > /dev/null && echo "$(GREEN)✓ Frontend healthy$(NC)" || echo "$(RED)✗ Frontend unhealthy$(NC)"

## ps: Show running containers
ps:
	docker compose ps

## db-migrate: Run database migrations
db-migrate:
	@echo "$(BLUE)Running database migrations...$(NC)"
	docker compose exec backend alembic upgrade head
	@echo "$(GREEN)Migrations complete!$(NC)"

## db-backup: Backup PostgreSQL database
db-backup:
	@echo "$(BLUE)Backing up database...$(NC)"
	@mkdir -p backups
	docker compose exec -T postgres pg_dump -U rag_fortress rag_fortress > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)Backup complete! Check backups/ directory$(NC)"

## db-restore: Restore PostgreSQL database from latest backup
db-restore:
	@echo "$(RED)WARNING: This will restore the latest backup!$(NC)"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read confirm
	@echo "$(BLUE)Restoring database...$(NC)"
	@LATEST=$$(ls -t backups/*.sql | head -1); \
	if [ -z "$$LATEST" ]; then \
		echo "$(RED)No backup files found in backups/$(NC)"; \
		exit 1; \
	fi; \
	echo "Restoring from $$LATEST"; \
	docker compose exec -T postgres psql -U rag_fortress rag_fortress < $$LATEST
	@echo "$(GREEN)Restore complete!$(NC)"

## db-shell: Open PostgreSQL shell
db-shell:
	@echo "$(BLUE)Opening PostgreSQL shell...$(NC)"
	docker compose exec postgres psql -U rag_fortress rag_fortress

## redis-cli: Open Redis CLI
redis-cli:
	@echo "$(BLUE)Opening Redis CLI...$(NC)"
	docker compose exec redis redis-cli

## shell-backend: Open shell in backend container
shell-backend:
	@echo "$(BLUE)Opening backend shell...$(NC)"
	docker compose exec backend /bin/bash

## clean: Stop and remove containers
clean:
	@echo "$(BLUE)Cleaning up containers...$(NC)"
	docker compose down --remove-orphans
	@echo "$(GREEN)Cleanup complete!$(NC)"

## clean-volumes: Remove all volumes (DANGER - deletes all data!)
clean-volumes:
	@echo "$(RED)WARNING: This will delete ALL data including databases!$(NC)"
	@echo "Type 'yes' to confirm: "
	@read confirm; \
	if [ "$$confirm" = "yes" ]; then \
		docker compose down -v; \
		echo "$(GREEN)Volumes removed!$(NC)"; \
	else \
		echo "$(BLUE)Cancelled.$(NC)"; \
	fi

## prune: Remove unused Docker resources
prune:
	@echo "$(BLUE)Removing unused Docker resources...$(NC)"
	docker system prune -f
	@echo "$(GREEN)Cleanup complete!$(NC)"

## update: Pull latest images and rebuild
update:
	@echo "$(BLUE)Updating services...$(NC)"
	docker compose pull
	docker compose up -d --build
	@echo "$(GREEN)Update complete!$(NC)"

## test-backend: Run backend tests
test-backend:
	@echo "$(BLUE)Running backend tests...$(NC)"
	docker compose exec backend pytest

## exec-backend: Execute command in backend container
# Usage: make exec-backend CMD="python script.py"
exec-backend:
	@echo "$(BLUE)Executing in backend: $(CMD)$(NC)"
	docker compose exec backend $(CMD)

## scale: Scale backend service
# Usage: make scale NUM=3
scale:
	@echo "$(BLUE)Scaling backend to $(NUM) instances...$(NC)"
	docker compose up -d --scale backend=$(NUM)
