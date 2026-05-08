# Makefile for lights-off
# Deps and metadata are in pyproject.toml.
#
# Usage:
#   make venv          — create .venv (once)
#   make install       — install all runtime + dev deps
#   make install-full  — also install GUI/audio libs (needs display on Linux)
#   make test          — run unit tests (no network)
#   make test-live     — run unit + live Mastodon API tests (requires .env)
#   make run           — launch the app
#   make lint          — run pyflakes
#   make build         — build wheel + sdist
#   make clean         — remove .venv, build artefacts, caches

PYTHON   := python
VENV     := .venv
PIP      := $(VENV)/Scripts/pip
PYTEST   := $(VENV)/Scripts/pytest
PYFLAKES := $(VENV)/Scripts/pyflakes

.PHONY: all venv install install-full test test-live run lint build clean help

all: install test

# ── Virtual environment ───────────────────────────────────────────────────────

venv:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip

# ── Dependencies ──────────────────────────────────────────────────────────────

install: venv
	$(PIP) install -e ".[dev]"
	$(PIP) install git+https://github.com/accessibleapps/keyboard_handler
	@echo "Dependencies installed."

install-full: install
	$(PIP) install wxpython
	@echo "Full install complete (GUI/audio included)."

# ── Tests ─────────────────────────────────────────────────────────────────────

test:
	$(PYTEST) tests/test_utils.py tests/test_mastodon_account.py -v

test-live:
	$(PYTEST) tests/ -v

# ── Run ───────────────────────────────────────────────────────────────────────

run:
	$(VENV)/Scripts/python -m lights_off

# ── Lint ──────────────────────────────────────────────────────────────────────

lint:
	$(PYFLAKES) lights_off/

# ── Build (wheel + sdist for PyPI) ───────────────────────────────────────────

build: venv
	$(PIP) install --upgrade build
	$(VENV)/Scripts/python -m build

# ── Clean ─────────────────────────────────────────────────────────────────────

clean:
	rm -rf $(VENV) .pytest_cache dist build *.egg-info
	find . -type d -name __pycache__ ! -path "./.git/*" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned."

# ── Help ──────────────────────────────────────────────────────────────────────

help:
	@echo ""
	@echo "  make venv          Create .venv"
	@echo "  make install       Install all deps from pyproject.toml"
	@echo "  make install-full  Also install wxpython (needs display on Linux)"
	@echo "  make test          Run unit tests (no network)"
	@echo "  make test-live     Run all tests including live Mastodon API"
	@echo "  make run           Launch lights-off"
	@echo "  make lint          Run pyflakes"
	@echo "  make build         Build wheel + sdist for PyPI"
	@echo "  make clean         Remove .venv, build artefacts, caches"
	@echo ""
	@echo "  Existing .bat scripts:"
	@echo "  build.bat          Nuitka standalone Windows build"
	@echo "  run.bat            Run via system Python (no venv)"
	@echo "  copy.bat           Assemble windist/ release folder"
	@echo ""
