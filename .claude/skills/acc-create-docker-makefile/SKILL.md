---
name: acc-create-docker-makefile
description: Generates Docker Makefile with common commands for PHP projects. Creates build, run, test, and deployment targets.
---

# Docker Makefile Generator

Generates a comprehensive Makefile for managing Docker-based PHP projects.

## Generated Files

```
Makefile                    # Docker project management targets
```

## Complete Makefile Template

```makefile
# ──────────────────────────────────────────────────────────
# Docker Makefile for PHP Project
# Usage: make <target>
# ──────────────────────────────────────────────────────────

# ─── Variables ────────────────────────────────────────────
COMPOSE_FILE      ?= docker-compose.yml
COMPOSE_FILE_DEV  ?= docker-compose.dev.yml
COMPOSE_FILE_CI   ?= docker-compose.ci.yml
PHP_SERVICE       ?= php
NGINX_SERVICE     ?= nginx
DB_SERVICE        ?= mysql
REDIS_SERVICE     ?= redis
RABBITMQ_SERVICE  ?= rabbitmq
COMPOSE           = docker compose -f $(COMPOSE_FILE)
COMPOSE_DEV       = docker compose -f $(COMPOSE_FILE) -f $(COMPOSE_FILE_DEV)
COMPOSE_CI        = docker compose -f $(COMPOSE_FILE_CI)
PHP_EXEC          = $(COMPOSE) exec $(PHP_SERVICE)
PHP_RUN           = $(COMPOSE) run --rm $(PHP_SERVICE)
COMPOSER          = $(PHP_EXEC) composer

# ─── Colors ───────────────────────────────────────────────
GREEN  = \033[0;32m
YELLOW = \033[0;33m
CYAN   = \033[0;36m
RESET  = \033[0m

# ──────────────────────────────────────────────────────────
# BUILD
# ──────────────────────────────────────────────────────────
.PHONY: build build-dev build-ci build-no-cache

build: ## Build production images
	@echo "$(GREEN)Building production images...$(RESET)"
	$(COMPOSE) build

build-dev: ## Build development images
	@echo "$(GREEN)Building development images...$(RESET)"
	$(COMPOSE_DEV) build

build-ci: ## Build CI images
	@echo "$(GREEN)Building CI images...$(RESET)"
	$(COMPOSE_CI) build

build-no-cache: ## Build images without cache
	@echo "$(YELLOW)Building images without cache...$(RESET)"
	$(COMPOSE) build --no-cache

# ──────────────────────────────────────────────────────────
# LIFECYCLE
# ──────────────────────────────────────────────────────────
.PHONY: up up-dev down restart stop status logs

up: ## Start all services
	@echo "$(GREEN)Starting services...$(RESET)"
	$(COMPOSE) up -d

up-dev: ## Start services in development mode
	@echo "$(GREEN)Starting development services...$(RESET)"
	$(COMPOSE_DEV) up -d

down: ## Stop and remove containers, networks
	@echo "$(YELLOW)Stopping services...$(RESET)"
	$(COMPOSE) down

restart: down up ## Restart all services

stop: ## Stop services without removing
	$(COMPOSE) stop

status: ## Show running containers and their status
	@echo "$(CYAN)Container status:$(RESET)"
	$(COMPOSE) ps

logs: ## Show logs from all services
	$(COMPOSE) logs -f --tail=100

logs-php: ## Show PHP service logs
	$(COMPOSE) logs -f --tail=100 $(PHP_SERVICE)

logs-nginx: ## Show Nginx service logs
	$(COMPOSE) logs -f --tail=100 $(NGINX_SERVICE)

# ──────────────────────────────────────────────────────────
# SHELL ACCESS
# ──────────────────────────────────────────────────────────
.PHONY: shell shell-root shell-db shell-redis

shell: ## Open shell in PHP container
	$(PHP_EXEC) sh

shell-root: ## Open root shell in PHP container
	$(COMPOSE) exec -u root $(PHP_SERVICE) sh

shell-db: ## Open database CLI
	$(COMPOSE) exec $(DB_SERVICE) mysql -u root -p

shell-redis: ## Open Redis CLI
	$(COMPOSE) exec $(REDIS_SERVICE) redis-cli

# ──────────────────────────────────────────────────────────
# TESTING
# ──────────────────────────────────────────────────────────
.PHONY: test test-unit test-integration test-coverage test-ci

test: ## Run all tests
	@echo "$(GREEN)Running tests...$(RESET)"
	$(PHP_EXEC) vendor/bin/phpunit

test-unit: ## Run unit tests only
	@echo "$(GREEN)Running unit tests...$(RESET)"
	$(PHP_EXEC) vendor/bin/phpunit --group=unit

test-integration: ## Run integration tests only
	@echo "$(GREEN)Running integration tests...$(RESET)"
	$(PHP_EXEC) vendor/bin/phpunit --group=integration

test-coverage: ## Run tests with coverage report
	@echo "$(GREEN)Running tests with coverage...$(RESET)"
	$(PHP_EXEC) vendor/bin/phpunit --coverage-html=coverage --coverage-clover=coverage/clover.xml

test-ci: build-ci ## Run tests in CI environment
	@echo "$(GREEN)Running CI tests...$(RESET)"
	$(COMPOSE_CI) run --rm app vendor/bin/phpunit --coverage-clover=coverage/clover.xml

# ──────────────────────────────────────────────────────────
# STATIC ANALYSIS & LINTING
# ──────────────────────────────────────────────────────────
.PHONY: lint phpstan cs-fix cs-check psalm

lint: phpstan cs-check ## Run all linters

phpstan: ## Run PHPStan static analysis
	@echo "$(GREEN)Running PHPStan...$(RESET)"
	$(PHP_EXEC) vendor/bin/phpstan analyse --memory-limit=512M

cs-fix: ## Fix code style with PHP CS Fixer
	@echo "$(GREEN)Fixing code style...$(RESET)"
	$(PHP_EXEC) vendor/bin/php-cs-fixer fix

cs-check: ## Check code style (dry-run)
	@echo "$(GREEN)Checking code style...$(RESET)"
	$(PHP_EXEC) vendor/bin/php-cs-fixer fix --dry-run --diff

psalm: ## Run Psalm type checker
	@echo "$(GREEN)Running Psalm...$(RESET)"
	$(PHP_EXEC) vendor/bin/psalm --show-info=true

# ──────────────────────────────────────────────────────────
# DATABASE
# ──────────────────────────────────────────────────────────
.PHONY: db-migrate db-migrate-down db-seed db-reset db-diff

db-migrate: ## Run database migrations
	@echo "$(GREEN)Running migrations...$(RESET)"
	$(PHP_EXEC) php bin/console doctrine:migrations:migrate --no-interaction

db-migrate-down: ## Rollback last migration
	@echo "$(YELLOW)Rolling back last migration...$(RESET)"
	$(PHP_EXEC) php bin/console doctrine:migrations:migrate prev --no-interaction

db-seed: ## Seed database with fixtures
	@echo "$(GREEN)Seeding database...$(RESET)"
	$(PHP_EXEC) php bin/console doctrine:fixtures:load --no-interaction

db-reset: ## Drop, create and migrate database
	@echo "$(YELLOW)Resetting database...$(RESET)"
	$(PHP_EXEC) php bin/console doctrine:database:drop --force --if-exists
	$(PHP_EXEC) php bin/console doctrine:database:create
	$(PHP_EXEC) php bin/console doctrine:migrations:migrate --no-interaction

db-diff: ## Generate migration from entity changes
	$(PHP_EXEC) php bin/console doctrine:migrations:diff

# ──────────────────────────────────────────────────────────
# CACHE
# ──────────────────────────────────────────────────────────
.PHONY: cache-clear cache-warmup

cache-clear: ## Clear application cache
	@echo "$(GREEN)Clearing cache...$(RESET)"
	$(PHP_EXEC) php bin/console cache:clear

cache-warmup: ## Warmup application cache
	@echo "$(GREEN)Warming up cache...$(RESET)"
	$(PHP_EXEC) php bin/console cache:warmup

# ──────────────────────────────────────────────────────────
# COMPOSER
# ──────────────────────────────────────────────────────────
.PHONY: composer-install composer-update composer-require composer-dump

composer-install: ## Install Composer dependencies
	@echo "$(GREEN)Installing dependencies...$(RESET)"
	$(COMPOSER) install

composer-update: ## Update Composer dependencies
	@echo "$(YELLOW)Updating dependencies...$(RESET)"
	$(COMPOSER) update

composer-require: ## Add a new dependency (usage: make composer-require PACKAGE=vendor/package)
	$(COMPOSER) require $(PACKAGE)

composer-dump: ## Regenerate autoloader
	$(COMPOSER) dump-autoload --optimize

# ──────────────────────────────────────────────────────────
# DOCKER CLEANUP
# ──────────────────────────────────────────────────────────
.PHONY: docker-clean docker-prune docker-volumes-clean

docker-clean: down ## Remove containers, images, and volumes for this project
	@echo "$(YELLOW)Cleaning project Docker resources...$(RESET)"
	$(COMPOSE) down --rmi local --volumes --remove-orphans

docker-prune: ## Remove all unused Docker resources (system-wide)
	@echo "$(YELLOW)Pruning unused Docker resources...$(RESET)"
	docker system prune -f
	docker volume prune -f

docker-volumes-clean: ## Remove project volumes
	@echo "$(YELLOW)Removing project volumes...$(RESET)"
	$(COMPOSE) down --volumes

# ──────────────────────────────────────────────────────────
# HELP
# ──────────────────────────────────────────────────────────
.PHONY: help
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "$(CYAN)Available targets:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-22s$(RESET) %s\n", $$1, $$2}'
```

## Generation Instructions

1. **Detect project setup:**
   - Check for existing docker-compose files
   - Identify service names (PHP, Nginx, DB, Redis)
   - Detect framework (Symfony/Laravel) for correct CLI commands

2. **Customize targets:**
   - Adapt database commands for framework (Doctrine/Eloquent)
   - Adapt cache commands for framework
   - Add project-specific services

3. **Set variables:**
   - Match COMPOSE_FILE to actual filenames
   - Match service names to docker-compose service names
   - Adjust PHP_EXEC for service name

4. **Validate:**
   - Ensure all referenced compose files exist
   - Verify service names match
   - Test each target works

## Usage

Provide:
- Framework (Symfony/Laravel)
- Docker Compose file names
- Service names
- Additional custom targets needed

The generator will:
1. Create Makefile with all standard targets
2. Adapt commands for the detected framework
3. Include proper .PHONY declarations
4. Add auto-generated help target
