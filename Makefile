VENV_DIR := .venv
PYTHON := python3
VENV_PYTHON := $(VENV_DIR)/bin/python
VENV_PIP := $(VENV_DIR)/bin/pip
OLLAMA_URL := http://localhost:11434

.PHONY: help setup ollama run clean

help:
	@echo "Targets:"
	@echo "  make setup  - create venv, install dependencies, create .env"
	@echo "  make run    - ensure Ollama is running and run the app"
	@echo "  make clean  - remove the venv and __pycache__ directories"

setup:
	@READY=1; \
	echo "[1/3] Creating virtual environment..."; \
	if [ -d $(VENV_DIR) ]; then \
		echo ".venv already exists, skipping creation."; \
	else \
		$(PYTHON) -m venv $(VENV_DIR); \
		READY=0; \
	fi; \
	echo "[2/3] Checking dependencies..."; \
	if $(VENV_PIP) show $$(cat requirements.txt) >/dev/null 2>&1; then \
		echo "All dependencies are already installed."; \
	else \
		echo "Installing dependencies..."; \
		$(VENV_PIP) install -r requirements.txt; \
		READY=0; \
	fi; \
	echo "[3/3] Checking .env file..."; \
	if [ -f .env ]; then \
		echo ".env file already exists."; \
	else \
		printf 'OLLAMA_MODEL=llama3.2\nOLLAMA_BASE_URL=%s\n\nAPPINSIGHT_LOCAL=true\nAPPINSIGHT_APP_ID=\nAPPINSIGHT_API_KEY=\n' "$(OLLAMA_URL)" > .env; \
		echo ".env file created."; \
		READY=0; \
	fi; \
	echo ""; \
	if [ "$$READY" = "1" ]; then \
		echo "Everything is already installed. You can run 'make run'."; \
	else \
		echo "Setup complete! You can now run 'make run'."; \
	fi

ollama:
	@echo "Checking Ollama..."
	@if ! command -v ollama >/dev/null 2>&1; then \
		echo "Ollama not found. Installing..."; \
		curl -fsSL https://ollama.com/install.sh | sh; \
	fi
	@if ! curl -s $(OLLAMA_URL) >/dev/null 2>&1; then \
		echo "Starting Ollama..."; \
		nohup ollama serve >/tmp/ollama.log 2>&1 & \
		until curl -s $(OLLAMA_URL) >/dev/null 2>&1; do sleep 1; done; \
		echo "Ollama is running."; \
	else \
		echo "Ollama is already running."; \
	fi

run: ollama
	@if [ ! -d $(VENV_DIR) ]; then \
		echo "Virtual environment not found. Please run 'make setup' first."; \
		exit 1; \
	fi
	@if [ ! -f .env ]; then \
		echo ".env file not found. Please run 'make setup' first."; \
		exit 1; \
	fi
	@set -a; . ./.env; set +a; $(VENV_PYTHON) app.py

clean:
	rm -rf $(VENV_DIR)
	find . -type d -name __pycache__ -exec rm -rf {} +
