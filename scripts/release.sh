#!/usr/bin/env bash
#
# Cut a modric-cli release: pick a version (prompted, patch-bump suggested), bump
# pyproject.toml + __init__.py, commit, build wheel+sdist, write SHA256SUMS, tag, push,
# and publish a GitHub release with the artifacts attached. The install one-liner
# (scripts/install.sh) downloads the wheel from that release.
#
# Usage:
#   scripts/release.sh [VERSION]     # VERSION optional; prompts if omitted
#
# Env: MODRIC_CLI_REPO (default mangosteen-lab/modric-cli), PYTHON, NOTES.
# Prereqs: gh CLI logged in, clean working tree, push access.
set -euo pipefail
cd "$(dirname "$0")/.."

REPO="${MODRIC_CLI_REPO:-mangosteen-lab/modric-cli}"
PY="${PYTHON:-python3}"

pyproject_version() {
    "$PY" -c "import tomllib;print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])"
}
_sha256() {
    if command -v sha256sum >/dev/null 2>&1; then sha256sum "$@"; else shasum -a 256 "$@"; fi
}

# --- preflight -------------------------------------------------------------
command -v gh >/dev/null       || { echo "error: gh CLI not found"; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "error: not logged in — run: gh auth login"; exit 1; }
if [ -n "$(git status --porcelain)" ]; then
    echo "error: working tree is not clean — commit or stash first (dist/ is ignored)."; exit 1
fi

# --- choose the version (patch bump suggested; current if not yet tagged) --
CURRENT="$(pyproject_version)"
if git rev-parse -q --verify "refs/tags/v$CURRENT" >/dev/null; then
    SUGGESTED="$(echo "$CURRENT" | awk -F. '{printf "%d.%d.%d", $1, $2, ($3+1)}')"
else
    SUGGESTED="$CURRENT"     # current version has never been released
fi
REQUESTED="${1:-}"; REQUESTED="${REQUESTED#v}"
if [ -z "$REQUESTED" ]; then
    read -r -p "Version to release [$SUGGESTED]: " REQUESTED
    REQUESTED="${REQUESTED:-$SUGGESTED}"
fi

# --- bump + commit (so the built artifacts carry this version) -------------
if [ "$REQUESTED" != "$CURRENT" ]; then
    echo ">> Bumping $CURRENT -> $REQUESTED"
    "$PY" - "$REQUESTED" <<'PY'
import pathlib, re, sys
v = sys.argv[1]
pp = pathlib.Path("pyproject.toml")
text, n = re.subn(r'(?m)^version\s*=\s*".*"$', f'version = "{v}"', pp.read_text(), count=1)
assert n == 1, "could not find a single version line in pyproject.toml"
pp.write_text(text)
init = pathlib.Path("modric_cli/__init__.py")
text2, n2 = re.subn(r'(?m)^(\s*__version__\s*=\s*)".*"$', rf'\g<1>"{v}"', init.read_text(), count=1)
assert n2 == 1, "could not find the __version__ fallback in modric_cli/__init__.py"
init.write_text(text2)
PY
    git commit -aqm "Release $REQUESTED"
fi

VERSION="$(pyproject_version)"
TAG="v$VERSION"
echo ">> Releasing $REPO @ $TAG"

# --- build wheel + sdist, verify the wheel carries this version ------------
rm -rf dist
"$PY" -m pip install --quiet build >/dev/null
"$PY" -m build >/dev/null
WHEEL="dist/modric_cli-$VERSION-py3-none-any.whl"
SDIST="dist/modric_cli-$VERSION.tar.gz"
[ -f "$WHEEL" ] || { echo "error: expected $WHEEL after build"; exit 1; }
[ -f "$SDIST" ] || { echo "error: expected $SDIST after build"; exit 1; }
( cd dist && _sha256 "modric_cli-$VERSION-py3-none-any.whl" "modric_cli-$VERSION.tar.gz" \
    > SHA256SUMS )

# --- tag, push commit + tag ------------------------------------------------
git rev-parse -q --verify "refs/tags/$TAG" >/dev/null || git tag "$TAG"
git push origin HEAD
git push origin "$TAG"

# --- publish the release (or re-upload assets if it already exists) --------
if gh release view "$TAG" --repo "$REPO" >/dev/null 2>&1; then
    echo ">> Release $TAG exists; uploading/overwriting the assets."
    gh release upload "$TAG" "$WHEEL" "$SDIST" dist/SHA256SUMS --repo "$REPO" --clobber
else
    gh release create "$TAG" "$WHEEL" "$SDIST" dist/SHA256SUMS \
        --repo "$REPO" --title "modric-cli $VERSION" --notes "${NOTES:-modric-cli $VERSION}"
fi

cat <<EOF

Release published: https://github.com/$REPO/releases/tag/$TAG

Install (no clone):
  curl -fsSL https://raw.githubusercontent.com/$REPO/master/scripts/install.sh | sh

Pin a version:  MODRIC_CLI_VERSION=$VERSION curl -fsSL .../install.sh | sh
EOF
