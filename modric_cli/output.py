"""Output helpers: JSON (default, agent-friendly) or a compact table view."""
from __future__ import annotations

import json
import sys


def emit(obj, as_json: bool = True) -> None:
    """Print a result. JSON is the default because it's the most reliable thing for a
    code agent to parse; --table renders a human-friendly grid for list-of-dict results."""
    if as_json or not (isinstance(obj, list) and obj and isinstance(obj[0], dict)):
        print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))
        return
    _table(obj, list(obj[0].keys()))


def _table(rows: list, columns: list[str]) -> None:
    if not rows:
        print("(no results)")
        return
    widths = {c: len(c) for c in columns}
    cells = []
    for row in rows:
        cell = {c: _fmt(row.get(c, "")) for c in columns}
        for c in columns:
            widths[c] = max(widths[c], len(cell[c]))
        cells.append(cell)
    line = "  ".join(c.ljust(widths[c]) for c in columns)
    print(line)
    print("  ".join("-" * widths[c] for c in columns))
    for cell in cells:
        print("  ".join(cell[c].ljust(widths[c]) for c in columns))


def _fmt(v) -> str:
    if isinstance(v, (dict, list)):
        return json.dumps(v, default=str)
    return "" if v is None else str(v)


def die(message: str, code: int = 1) -> None:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(code)
