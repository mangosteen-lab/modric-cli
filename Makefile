# modric-cli — build / test / install targets.
# The CLI has zero runtime dependencies (Python stdlib only); dev tools are optional.

PYTHON ?= python3

.PHONY: help build test lint install uninstall install-skill uninstall-skill clean

help:
	@echo "Targets:"
	@echo "  make install          Install the 'modric' command (pipx if present, else pip --user)"
	@echo "  make uninstall        Remove the 'modric' command"
	@echo "  make install-skill    Install modric-cli as a Claude Code / Codex skill"
	@echo "  make uninstall-skill  Remove the installed skill"
	@echo "  make test             Run the test suite"
	@echo "  make lint             Ruff lint"
	@echo "  make build            Build sdist + wheel into dist/"
	@echo "  make clean            Remove build artifacts"

build:
	$(PYTHON) -m pip install --quiet build && $(PYTHON) -m build

test:
	$(PYTHON) -m pytest tests -q

lint:
	$(PYTHON) -m ruff check modric_cli tests

install:
	@sh scripts/install.sh

uninstall:
	@sh scripts/uninstall.sh

install-skill:
	@sh scripts/install-skill.sh all

uninstall-skill:
	@sh scripts/uninstall-skill.sh all

clean:
	rm -rf dist build *.egg-info modric_cli/__pycache__ tests/__pycache__ .pytest_cache
