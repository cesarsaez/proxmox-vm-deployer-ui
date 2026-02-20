.PHONY: help start stop restart logs install build clean docker-up docker-down docker-logs docker-build test

help:
	@echo "Proxmox VM Deployer - Available Commands"
	@echo ""
	@echo "Development:"
	@echo "  make start          - Start backend and frontend (development mode)"
	@echo "  make stop           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View logs (tail -f)"
	@echo "  make install        - Install dependencies"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up      - Start with Docker Compose"
	@echo "  make docker-down    - Stop Docker containers"
	@echo "  make docker-logs    - View Docker logs"
	@echo "  make docker-build   - Rebuild Docker images"
	@echo "  make docker-restart - Restart Docker containers"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean          - Clean logs and cache files"
	@echo "  make test           - Run tests (if configured)"
	@echo ""

# Development commands
start:
	@echo "Starting Proxmox VM Deployer..."
	@./start.sh

stop:
	@echo "Stopping Proxmox VM Deployer..."
	@./stop.sh

restart: stop start

logs:
	@echo "Press Ctrl+C to stop following logs"
	@tail -f logs/backend.log logs/frontend.log

install:
	@echo "Installing backend dependencies..."
	@cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	@cd frontend && npm install
	@echo "Dependencies installed successfully!"

# Docker commands
docker-up:
	@echo "Starting with Docker Compose..."
	@docker-compose up -d
	@echo "Services started!"
	@echo "Frontend: http://localhost:3001"
	@echo "Backend: http://localhost:8000"

docker-down:
	@echo "Stopping Docker containers..."
	@docker-compose down

docker-logs:
	@docker-compose logs -f

docker-build:
	@echo "Rebuilding Docker images..."
	@docker-compose build --no-cache

docker-restart:
	@docker-compose restart

# Maintenance commands
clean:
	@echo "Cleaning logs and cache..."
	@rm -rf logs/*.log
	@rm -rf backend/__pycache__
	@rm -rf backend/app/__pycache__
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@echo "Clean complete!"

test:
	@echo "Running tests..."
	@echo "No tests configured yet"

# Setup commands
setup-env:
	@if [ ! -f backend/.env ]; then \
		cp backend/.env.example backend/.env; \
		echo "Created backend/.env - Please edit with your Proxmox credentials"; \
	else \
		echo "backend/.env already exists"; \
	fi

# Full setup
setup: setup-env install
	@echo ""
	@echo "Setup complete!"
	@echo "1. Edit backend/.env with your Proxmox credentials"
	@echo "2. Run 'make start' to start the application"
