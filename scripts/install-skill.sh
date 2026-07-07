#!/usr/bin/env sh
# Install modric-cli as a skill for external code agents (macOS/Linux).
#
#   No clone:      curl -fsSL https://raw.githubusercontent.com/mangosteen-lab/modric-cli/master/scripts/install-skill.sh | sh -s -- all
#   From checkout: scripts/install-skill.sh [claude|codex|all]   (default: all)
#
# Env: MODRIC_CLI_REPO, MODRIC_CLI_BRANCH (default: master).
set -eu

REPO="${MODRIC_CLI_REPO:-mangosteen-lab/modric-cli}"
BRANCH="${MODRIC_CLI_BRANCH:-master}"
TARGET="${1:-all}"

REPO_DIR=""
SELF="${0:-}"
if [ -f "$SELF" ]; then
    SD="$(CDPATH= cd -- "$(dirname -- "$SELF")" && pwd)"
    [ -f "$SD/../pyproject.toml" ] && REPO_DIR="$(dirname "$SD")"
fi

fetch() {   # $1 = repo-relative path, $2 = destination file
    if [ -n "$REPO_DIR" ]; then
        cp "$REPO_DIR/$1" "$2"
    else
        curl -fsSL "https://raw.githubusercontent.com/$REPO/$BRANCH/$1" -o "$2"
    fi
}

install_claude() {
    dest="${CLAUDE_HOME:-$HOME/.claude}/skills/modric-troubleshooting"
    mkdir -p "$dest"
    fetch "skills/claude-code/SKILL.md" "$dest/SKILL.md"
    echo "Claude Code skill installed -> $dest/SKILL.md"
}

install_codex() {
    dir="${CODEX_HOME:-$HOME/.codex}"
    mkdir -p "$dir"
    marker="<!-- modric-cli:begin -->"
    if [ -f "$dir/AGENTS.md" ] && grep -qF "$marker" "$dir/AGENTS.md"; then
        echo "Codex snippet already present in $dir/AGENTS.md (skipping)"
        return
    fi
    tmp="$(mktemp)"
    fetch "skills/codex/AGENTS-snippet.md" "$tmp"
    { echo ""; echo "$marker"; cat "$tmp"; echo "<!-- modric-cli:end -->"; } >> "$dir/AGENTS.md"
    rm -f "$tmp"
    echo "Codex guidance appended -> $dir/AGENTS.md"
}

case "$TARGET" in
    claude) install_claude ;;
    codex)  install_codex ;;
    all)    install_claude; install_codex ;;
    *) echo "usage: install-skill.sh [claude|codex|all]" >&2; exit 2 ;;
esac
