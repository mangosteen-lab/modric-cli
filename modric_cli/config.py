"""Config file handling: where the Modric URL + API token are stored.

Precedence for both url and token: explicit CLI flag > environment variable
(MODRIC_URL / MODRIC_TOKEN) > config file. The token is written with 0600
permissions so it isn't world-readable.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

ENV_URL = "MODRIC_URL"
ENV_TOKEN = "MODRIC_TOKEN"


def config_path() -> Path:
    """Platform-appropriate config file location (override with MODRIC_CONFIG)."""
    override = os.environ.get("MODRIC_CONFIG")
    if override:
        return Path(override)
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "modric" / "config.json"


def load() -> dict:
    path = config_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save(url: str, token: str) -> Path:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"url": url, "token": token}, indent=2), encoding="utf-8")
    try:
        os.chmod(path, 0o600)   # best effort; no-op semantics vary on Windows
    except OSError:
        pass
    return path


def resolve(url_flag: str | None = None, token_flag: str | None = None) -> tuple[str, str]:
    """Return (url, token), applying flag > env > file precedence."""
    cfg = load()
    url = url_flag or os.environ.get(ENV_URL) or cfg.get("url", "")
    token = token_flag or os.environ.get(ENV_TOKEN) or cfg.get("token", "")
    return url.rstrip("/"), token
