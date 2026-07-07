#!/usr/bin/env sh
# Uninstall the `modric` CLI (macOS/Linux).
set -eu
if command -v pipx >/dev/null 2>&1 && pipx list 2>/dev/null | grep -q modric-cli; then
    pipx uninstall modric-cli
else
    "${PYTHON:-python3}" -m pip uninstall -y modric-cli
fi
echo "Removed the 'modric' command. (Config at ~/.config/modric/config.json is left in place.)"
