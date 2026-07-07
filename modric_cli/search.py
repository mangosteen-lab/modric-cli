"""Shared search helpers with hard output caps.

Two guardrails keep an agent from pulling too much:
  * at most MAX_RESULTS (1000) results are ever returned, and
  * each result's `snippet` text is clamped to MAX_RESULT_BYTES (10 KB).
Content/log searches return a context window (`before`/`after` lines around each
match) instead of whole files or logs.
"""
from __future__ import annotations

import re

MAX_RESULTS = 1000
MAX_RESULT_BYTES = 10 * 1024


def compile_query(query: str, regex: bool = False, ignore_case: bool = True):
    flags = re.IGNORECASE if ignore_case else 0
    try:
        return re.compile(query if regex else re.escape(query), flags)
    except re.error as exc:
        from .client import ModricError
        raise ModricError(f"invalid regex: {exc}") from exc


def field_hit(value, rx) -> bool:
    return value is not None and rx.search(str(value)) is not None


def grep(text: str, rx, before: int = 0, after: int = 0) -> list[dict]:
    """Return a context block for every matching line: {line, snippet}."""
    lines = (text or "").splitlines()
    blocks = []
    for i, line in enumerate(lines):
        if rx.search(line):
            lo = max(0, i - max(before, 0))
            hi = min(len(lines), i + max(after, 0) + 1)
            snippet = "\n".join(f"{j + 1}: {lines[j]}" for j in range(lo, hi))
            blocks.append({"line": i + 1, "snippet": snippet})
    return blocks


class Collector:
    """Accumulates results and stops once MAX_RESULTS is reached."""
    def __init__(self, limit: int = MAX_RESULTS):
        self.limit = min(max(int(limit), 1), MAX_RESULTS)
        self.items: list[dict] = []
        self.truncated = False

    def add(self, result: dict) -> None:
        if len(self.items) >= self.limit:
            self.truncated = True
            return
        if isinstance(result.get("snippet"), str):
            result["snippet"] = _clamp(result["snippet"])
        self.items.append(result)

    @property
    def full(self) -> bool:
        return len(self.items) >= self.limit

    def result(self) -> dict:
        return {"returned": len(self.items), "truncated": self.truncated,
                "limit": self.limit, "results": self.items}


def _clamp(text: str) -> str:
    raw = text.encode("utf-8")
    if len(raw) <= MAX_RESULT_BYTES:
        return text
    return raw[:MAX_RESULT_BYTES].decode("utf-8", "ignore") + "\n…(truncated to 10 KB)"
