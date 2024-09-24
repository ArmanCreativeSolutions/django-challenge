# Makefile

# Variables
PROJECT_NAME = arman
PYTHON = python3
PIP = pip3
DJANGO_MANAGE = $(PYTHON) backend/manage.py
DOCKER_COMPOSE = docker compose

# Default environment file
ENV_FILE = .env

# Help command to display available tasks
.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make setup      		- Set up the project environment"
	@echo "  make run        		- Run the Django development server"
	@echo "  make migrate    		- Apply database migrations"
	@echo "  make superuser  		- Create a Django superuser"
	@echo "  make test       		- Run tests"
	@echo "  make lint       		- Lint the codebase"
	@echo "  make clean      		- Clean up project artifacts"
	@echo "  make docker-up  		- Start Docker services"
	@echo "  make docker-down		- Stop Docker services"
	@echo "  make docker-restart  	- Restart all Docker services"
	@echo "  make docker-logs     	- View logs for all Docker services"
	@echo "  make docker-migrate  	- Run Docker Django migrations"
	@echo "  make docker-superuser	- Create Docker Django superuser"
	@echo "  make docker-lint     	- Run Docker Django linter"
	@echo "  make docker-test     	- Run Docker Django tests"

# Set up the project environment
.PHONY: setup
setup:
	@echo "Setting up the project environment..."
	$(PIP) install -r backend/requirements.txt
	$(DJANGO_MANAGE) migrate
	$(DJANGO_MANAGE) collectstatic --noinput

# Run the Django development server
.PHONY: run
run:
	@echo "Starting the Django development server..."
	$(DJANGO_MANAGE) runserver 0.0.0.0:8000

# Apply migrations
.PHONY: migrate
migrate:
	@echo "Applying migrations..."
	$(DJANGO_MANAGE) migrate

# Create a Django superuser
.PHONY: superuser
superuser:
	@echo "Creating a Django superuser..."
	$(DJANGO_MANAGE) createsuperuser

# Run tests
.PHONY: test
test:
	@echo "Running tests..."
	$(DJANGO_MANAGE) test

# Lint the codebase
.PHONY: lint
lint:
	@echo "Running linter..."
	ruff format
	ruff check --fix

# Clean up the project directory
.PHONY: clean
clean:
	@echo "Cleaning up project artifacts..."
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete

# Run initial database setup (optional)
.PHONY: initdb
initdb:
	@echo "Initializing the database..."
	$(DJANGO_MANAGE) makemigrations
	$(DJANGO_MANAGE) migrate

# ---- Docker commands ----

# Start Docker services
.PHONY: docker-up
docker-up:
	@echo "Starting Docker services..."
	$(DOCKER_COMPOSE) up --build -d

# Stop Docker services
.PHONY: docker-down
docker-down:
	@echo "Stopping Docker services..."
	$(DOCKER_COMPOSE) down --remove-orphans

# Restart all services
.PHONY: docker-restart
docker-restart:
	$(DOCKER_COMPOSE) down && $(DOCKER_COMPOSE) up -d

# View logs
.PHONY: docker-logs
docker-logs:
	$(DOCKER_COMPOSE) logs -f

# Apply migrations
.PHONY: docker-migrate
docker-migrate:
	$(DOCKER_COMPOSE) exec backend python manage.py migrate

# Create superuser
.PHONY: docker-superuser
docker-superuser:
	$(DOCKER_COMPOSE) exec backend python manage.py createsuperuser

# Run linter
.PHONY: docker-lint
docker-lint:
	$(DOCKER_COMPOSE) exec backend ruff format && $(DOCKER_COMPOSE) exec backend ruff check --fix

# Run tests
.PHONY: docker-test
docker-test:
	$(DOCKER_COMPOSE) exec backend python manage.py test
