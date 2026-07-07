"""Small helpers for reading script content / JSON payloads from files or stdin."""
from __future__ import annotations

import json
import sys

from .client import ModricError


def read_text(file: str | None, inline: str | None) -> str:
    """Content precedence: --content inline > --file (path or '-' for stdin)."""
    if inline is not None:
        return inline
    if file == "-":
        return sys.stdin.read()
    if file:
        with open(file, encoding="utf-8") as fh:
            return fh.read()
    raise ModricError("provide --content or --file (use '-' to read stdin)")


def read_json(file: str | None) -> dict:
    if not file:
        raise ModricError("provide --file with a JSON document (use '-' for stdin)")
    raw = sys.stdin.read() if file == "-" else open(file, encoding="utf-8").read()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ModricError(f"invalid JSON in {file}: {exc}") from exc


def parse_kv(pairs: list[str] | None) -> dict:
    """Parse repeated KEY=VALUE flags into a dict."""
    out: dict = {}
    for item in pairs or []:
        if "=" not in item:
            raise ModricError(f"expected KEY=VALUE, got '{item}'")
        key, value = item.split("=", 1)
        out[key] = value
    return out
