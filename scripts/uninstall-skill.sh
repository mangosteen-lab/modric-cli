#!/usr/bin/env sh
# Remove the modric-cli agent skill (macOS/Linux).
#   scripts/uninstall-skill.sh [claude|codex|all]   (default: all)
set -eu
TARGET="${1:-all}"

remove_claude() {
    dest="${CLAUDE_HOME:-$HOME/.claude}/skills/modric-troubleshooting"
    rm -rf "$dest" && echo "Removed Claude Code skill ($dest)"
}

remove_codex() {
    f="${CODEX_HOME:-$HOME/.codex}/AGENTS.md"
    [ -f "$f" ] || return 0
    # Delete the block between our markers.
    sed '/<!-- modric-cli:begin -->/,/<!-- modric-cli:end -->/d' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
    echo "Removed Codex snippet from $f"
}

case "$TARGET" in
    claude) remove_claude ;;
    codex)  remove_codex ;;
    all)    remove_claude; remove_codex ;;
    *) echo "usage: $0 [claude|codex|all]" >&2; exit 2 ;;
esac
