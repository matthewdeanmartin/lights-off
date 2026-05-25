# Makefile for lights-off
# Deps and metadata are in pyproject.toml.
#
# Usage:
#   make install       — sync all runtime + dev deps
#   make install-full  — also install GUI/audio libs (needs display on Linux)
#   make test          — run unit tests (no network)
#   make test-live     — run live read-only tests (requires .env)
#   make test-live-write — run live tests that mutate data (requires .env)
#   make run           — launch the app
#   make lint          — run ruff
#   make build         — build wheel + sdist
#   make clean         — remove .venv, build artefacts, caches

UV := uv

.PHONY: all install install-full test test-live test-live-write run lint build clean help

all: install test

# ── Dependencies ──────────────────────────────────────────────────────────────

install:
	$(UV) sync --extra dev
	@echo "Dependencies installed."

install-full: install
	$(UV) pip install wxpython
	@echo "Full install complete (GUI/audio included)."

# ── Tests ─────────────────────────────────────────────────────────────────────

test:
	$(UV) run pytest tests/test_utils.py tests/test_mastodon_account.py -v

test-live:
	$(UV) run pytest tests/ -v -m "live and not live_write"

test-live-write:
	$(UV) run pytest tests/ -v -m "live_write"

# ── Run ───────────────────────────────────────────────────────────────────────

run:
	$(UV) run python -m lights_off

# ── Lint ──────────────────────────────────────────────────────────────────────

lint:
	$(UV) run ruff check lights_off/

# ── Build (wheel + sdist for PyPI) ───────────────────────────────────────────

build:
	$(UV) build

# ── Clean ─────────────────────────────────────────────────────────────────────

clean:
	rm -rf .venv .pytest_cache dist build *.egg-info
	find . -type d -name __pycache__ ! -path "./.git/*" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned."

# ── Help ──────────────────────────────────────────────────────────────────────

help:
	@echo ""
	@echo "  make install       Sync all deps from pyproject.toml"
	@echo "  make install-full  Also install wxpython (needs display on Linux)"
	@echo "  make test          Run unit tests (no network)"
	@echo "  make test-live     Run live read-only tests"
	@echo "  make test-live-write Run live tests that create or mutate data"
	@echo "  make run           Launch lights-off"
	@echo "  make lint          Run ruff"
	@echo "  make build         Build wheel + sdist for PyPI"
	@echo "  make clean         Remove .venv, build artefacts, caches"
	@echo ""

# ── Dogfooding targets (independent, not wired into check) ───────────────────

.PHONY: version-check
version-check:
	@$(UV) jiggle_version check

.PHONY: dev-status
dev-status:
	@$(UV) troml-dev-status validate .

.PHONY: prerelease-check
prerelease-check: version-check dev-status
	@echo "Pre-release checks passed."

.PHONY: dont-be-lazy
dont-be-lazy:
	@$(UV) dont_be_lazy --root . --no-color summary
	@$(UV) dont_be_lazy --root . --no-color scan lights_off --no-config-suppressions || true

.PHONY: pydoc-docs
pydoc-docs:
	@$(UV) pydoc_fork lights_off -o ./pydoc/
