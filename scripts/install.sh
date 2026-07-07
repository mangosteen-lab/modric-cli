#!/usr/bin/env sh
# Install the `modric` CLI on macOS/Linux. Prefers pipx (isolated) and falls back to
# `pip install --user`. Run from the repo root or via `make install`.
set -eu

REPO_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$REPO_DIR"

if command -v pipx >/dev/null 2>&1; then
    echo "Installing with pipx..."
    pipx install --force .
else
    PY="${PYTHON:-python3}"
    command -v "$PY" >/dev/null 2>&1 || { echo "error: python3 not found" >&2; exit 1; }
    echo "pipx not found; installing with $PY -m pip install --user ..."
    "$PY" -m pip install --user --upgrade .
    echo
    echo "If 'modric' is not found, add your user bin dir to PATH, e.g.:"
    echo "  export PATH=\"\$($PY -m site --user-base)/bin:\$PATH\""
fi

echo
echo "Installed. Next:"
echo "  modric auth login --url https://your-modric-host --token <API_TOKEN>"
echo "  modric --help"
