#!/usr/bin/env sh
# Install modric-cli as a skill for external code agents (macOS/Linux).
#   scripts/install-skill.sh [claude|codex|all]   (default: all)
set -eu

REPO_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
TARGET="${1:-all}"

install_claude() {
    dest="${CLAUDE_HOME:-$HOME/.claude}/skills/modric-troubleshooting"
    mkdir -p "$dest"
    cp "$REPO_DIR/skills/claude-code/SKILL.md" "$dest/SKILL.md"
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
    { echo ""; echo "$marker"; cat "$REPO_DIR/skills/codex/AGENTS-snippet.md";
      echo "<!-- modric-cli:end -->"; } >> "$dir/AGENTS.md"
    echo "Codex guidance appended -> $dir/AGENTS.md"
}

case "$TARGET" in
    claude) install_claude ;;
    codex)  install_codex ;;
    all)    install_claude; install_codex ;;
    *) echo "usage: $0 [claude|codex|all]" >&2; exit 2 ;;
esac
