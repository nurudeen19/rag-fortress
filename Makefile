# ============================================================================== 
# RAG Fortress - Docker Makefile
# ============================================================================== 

.PHONY: help setup setup-local build up down restart logs ps health db-migrate app-setup qdrant-dense qdrant-hybrid clean clean-volumes

BLUE := \033[0;34m
GREEN := \033[0;32m
RED := \033[0;31m
NC := \033[0m

.DEFAULT_GOAL := help

help:
	@echo "$(BLUE)RAG Fortress - Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Setup:$(NC)"
	@echo "  make setup          - Docker env files (.env.docker)"
	@echo "  make setup-local    - Local env files (.env)"
	@echo ""
	@echo "$(GREEN)Build & Run:$(NC)"
	@echo "  make build          - Build images"
	@echo "  make up             - Start services"
	@echo "  make down           - Stop services"
	@echo "  make restart        - Restart services"
	@echo "  make logs           - Follow logs"
	@echo "  make ps             - List containers"
	@echo "  make health         - Quick health check"
	@echo ""
	@echo "$(GREEN)Database:$(NC)"
	@echo "  make db-migrate     - Run migrations"
	@echo "  make app-setup      - Run setup.py with SETUP_ARGS"
	@echo "                      - Example: make app-setup SETUP_ARGS=\"--all\""
	@echo ""
	@echo "$(GREEN)Note: Use docker compose --profile qdrant-setup run --rm qdrant-setup for Qdrant init$(NC)"
	@echo ""
	@echo "$(GREEN)Cleanup:$(NC)"
	@echo "  make clean          - Stop and remove containers"
	@echo "  make clean-volumes  - Remove containers + volumes"
	@echo ""

setup:
	@echo "$(BLUE)Setting up Docker environment files...$(NC)"
	@test -f .env || (cp .env.docker.example .env && echo "$(GREEN)Created .env$(NC)")
	@test -f backend/.env.docker || (cp backend/.env.docker.example backend/.env.docker && echo "$(GREEN)Created backend/.env.docker$(NC)")
	@echo "$(GREEN)Docker setup complete! Edit .env and backend/.env.docker.$(NC)"

setup-local:
	@echo "$(BLUE)Setting up local environment files...$(NC)"
	@test -f backend/.env || (cp backend/.env.example backend/.env && echo "$(GREEN)Created backend/.env$(NC)")
	@test -f frontend/.env || (cp frontend/.env.example frontend/.env && echo "$(GREEN)Created frontend/.env$(NC)")
	@echo "$(GREEN)Local setup complete! Edit backend/.env and frontend/.env.$(NC)"

build:
	@echo "$(BLUE)Building images...$(NC)"
	docker compose build

up:
	@echo "$(BLUE)Starting services...$(NC)"
	docker compose up -d
	@echo "$(GREEN)Services started!$(NC)"

down:
	@echo "$(BLUE)Stopping services...$(NC)"
	docker compose down
	@echo "$(GREEN)Services stopped!$(NC)"

restart:
	@echo "$(BLUE)Restarting services...$(NC)"
	docker compose restart
	@echo "$(GREEN)Services restarted!$(NC)"

logs:
	docker compose logs -f

ps:
	docker compose ps

health:
	@echo "$(BLUE)Health checks:$(NC)"
	@docker compose exec -T backend curl -sf http://localhost:8000/health > /dev/null && echo "$(GREEN)Backend healthy$(NC)" || echo "$(RED)Backend unhealthy$(NC)"
	@docker compose exec -T frontend curl -sf http://localhost:3000/health > /dev/null && echo "$(GREEN)Frontend healthy$(NC)" || echo "$(RED)Frontend unhealthy$(NC)"

# ------------------------------------------------------------------------------
# Database
# ------------------------------------------------------------------------------

db-migrate:
	@echo "$(BLUE)Running database migrations...$(NC)"
	docker compose exec backend python migrate.py upgrade
	@echo "$(GREEN)Migrations complete!$(NC)"

app-setup:
	@echo "$(BLUE)Running setup.py...$(NC)"
	@docker compose exec backend python setup.py $(SETUP_ARGS)

# ------------------------------------------------------------------------------
# Qdrant collections (use init_qdrant.py via profiles instead)
# ------------------------------------------------------------------------------
# DEPRECATED: Use docker compose --profile qdrant-setup run --rm qdrant-setup
# These manual commands are kept for reference only

# ------------------------------------------------------------------------------
# Cleanup
# ------------------------------------------------------------------------------

clean:
	@echo "$(BLUE)Cleaning up containers...$(NC)"
	docker compose down --remove-orphans
	@echo "$(GREEN)Cleanup complete!$(NC)"

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
