# keyless-mcp developer commands. Run `make` to list them.
# Needs uv (https://docs.astral.sh/uv/). Everything else is installed by `make setup`.

export PATH := $(HOME)/.local/bin:$(PATH)
PY := .venv/bin/python
M3 := scripts/m3
TOOLSET ?= dev

.DEFAULT_GOAL := help
.PHONY: help setup test test-live record new-adapter lint fmt ui run tools

help: ## List the available commands
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-12s %s\n", $$1, $$2}'

setup: ## Install everything (Python 3.12 venv, dependencies, M3 SDK) and check it works
	uv sync --locked
	$(M3) setup --python $(PY)
	$(M3) doctor

test: ## Run all tests offline (replays cassettes; no network, no API keys)
	KEYLESS_MCP_HTTP_MODE=replay $(M3) test --python $(PY) -- m3_tests -m "not live and not agent" -q

test-live: ## Run the live smoke tests against the real APIs (needs network)
	KEYLESS_MCP_HTTP_MODE=live $(M3) test --python $(PY) -- m3_tests -m live -q

record: ## Re-record an adapter's cassettes from the real API: make record ADAPTER=arxiv
	@test -n "$(ADAPTER)" || { echo "usage: make record ADAPTER=<name>"; exit 1; }
	@test -d m3_tests/adapters/$(ADAPTER) || { echo "no such adapter: $(ADAPTER)"; exit 1; }
	rm -f m3_tests/adapters/$(ADAPTER)/cassettes/*.json
	KEYLESS_MCP_HTTP_MODE=record $(M3) test --python $(PY) -- m3_tests/adapters/$(ADAPTER) -m "not live and not agent" -q

new-adapter: ## Scaffold an adapter: make new-adapter NAME=open_meteo TOOLSET=geo
	@test -n "$(NAME)" || { echo "usage: make new-adapter NAME=<name> [TOOLSET=science|dev|geo|news]"; exit 1; }
	uv run python scripts/new_adapter.py $(NAME) --toolset $(TOOLSET)

lint: ## Check code style (ruff check + ruff format --check)
	uv run ruff check .
	uv run ruff format --check .

fmt: ## Auto-fix lint issues and format the code
	uv run ruff check --fix .
	uv run ruff format .

ui: ## Open the M3 results viewer for saved runs
	$(M3) ui

run: ## Start the server on stdio
	uv run keyless-mcp

tools: ## List every registered tool with its toolset
	uv run keyless-mcp --list-tools
