#!/usr/bin/env sh
# Install the `modric` CLI on macOS/Linux.
#
#   No clone (recommended):
#     curl -fsSL https://raw.githubusercontent.com/mangosteen-lab/modric-cli/master/scripts/install.sh | sh
#   From a checkout:
#     sh scripts/install.sh
#
# Env: MODRIC_CLI_VERSION (default: latest release), MODRIC_CLI_REPO, PYTHON,
#      MODRIC_CLI_FORCE_DOWNLOAD=1 (ignore a local checkout and fetch the release).
set -eu

REPO="${MODRIC_CLI_REPO:-mangosteen-lab/modric-cli}"

# Detect a local checkout (this script sitting in <repo>/scripts/ next to pyproject.toml).
REPO_DIR=""
SELF="${0:-}"
if [ -f "$SELF" ]; then
    SD="$(CDPATH= cd -- "$(dirname -- "$SELF")" && pwd)"
    [ -f "$SD/../pyproject.toml" ] && REPO_DIR="$(dirname "$SD")"
fi

_sha256() {
    if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'
    else shasum -a 256 "$1" | awk '{print $1}'; fi
}

_pip_install() {   # $1 = wheel path or source dir
    if command -v pipx >/dev/null 2>&1; then
        pipx install --force "$1"
    else
        PY="${PYTHON:-python3}"
        command -v "$PY" >/dev/null 2>&1 || { echo "error: python3 not found" >&2; exit 1; }
        "$PY" -m pip install --user --upgrade "$1"
        echo "If 'modric' is not found, add \"\$($PY -m site --user-base)/bin\" to PATH."
    fi
}

if [ -n "$REPO_DIR" ] && [ "${MODRIC_CLI_FORCE_DOWNLOAD:-}" != "1" ]; then
    echo "Installing from local checkout ($REPO_DIR)..."
    _pip_install "$REPO_DIR"
else
    VERSION="${MODRIC_CLI_VERSION:-}"
    if [ -z "$VERSION" ]; then
        echo "Resolving latest release of $REPO..."
        VERSION="$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" \
            | sed -n 's/.*"tag_name":[[:space:]]*"v\{0,1\}\([^"]*\)".*/\1/p' | head -1)"
        [ -n "$VERSION" ] || { echo "error: could not resolve latest release of $REPO" >&2; exit 1; }
    fi
    TAG="v$VERSION"
    WHEEL="modric_cli-$VERSION-py3-none-any.whl"
    BASE="https://github.com/$REPO/releases/download/$TAG"
    TMP="$(mktemp -d)"
    trap 'rm -rf "$TMP"' EXIT
    echo "Downloading $WHEEL ($TAG)..."
    curl -fsSL "$BASE/$WHEEL" -o "$TMP/$WHEEL"
    curl -fsSL "$BASE/SHA256SUMS" -o "$TMP/SHA256SUMS"
    expected="$(awk -v f="$WHEEL" '$2==f || $2=="*"f {print $1}' "$TMP/SHA256SUMS" | head -1)"
    [ -n "$expected" ] || { echo "error: $WHEEL not listed in SHA256SUMS" >&2; exit 1; }
    [ "$(_sha256 "$TMP/$WHEEL")" = "$expected" ] \
        || { echo "error: checksum mismatch for $WHEEL" >&2; exit 1; }
    echo "Checksum OK. Installing..."
    _pip_install "$TMP/$WHEEL"
fi

echo
echo "Installed. Next:"
echo "  modric auth login --url https://your-modric-host --token <API_TOKEN>"
echo "  modric --help"
