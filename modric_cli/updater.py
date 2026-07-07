"""Self-update: check the GitHub releases and pip-install a newer wheel.

modric-cli is distributed as a checksum-verified wheel attached to GitHub releases (it
is not on PyPI), so upgrading means fetching that wheel and reinstalling it into the
current interpreter. `modric upgrade` wraps exactly that.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request

from . import __version__
from .client import ModricError

DEFAULT_REPO = "mangosteen-lab/modric-cli"


def _repo() -> str:
    return os.environ.get("MODRIC_CLI_REPO", DEFAULT_REPO)


def _get(url: str, accept: str = "application/json") -> bytes:
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": "modric-cli"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()
    except Exception as exc:  # noqa: BLE001 - network/HTTP errors -> actionable message
        raise ModricError(f"cannot reach GitHub ({url}): {exc}") from exc


def latest_version() -> str:
    data = json.loads(_get(f"https://api.github.com/repos/{_repo()}/releases/latest"))
    tag = (data.get("tag_name") or "").lstrip("v")
    if not tag:
        raise ModricError("could not determine the latest release")
    return tag


def _parts(version: str) -> tuple:
    out = []
    for chunk in version.split("."):
        digits = "".join(c for c in chunk if c.isdigit())
        out.append(int(digits) if digits else 0)
    return tuple(out)


def is_newer(latest: str, current: str) -> bool:
    try:
        return _parts(latest) > _parts(current)
    except Exception:  # noqa: BLE001
        return latest != current


def _expected_hash(sums: str, wheel: str) -> str | None:
    for line in sums.splitlines():
        cols = line.split()
        if len(cols) >= 2 and cols[1].lstrip("*") == wheel:
            return cols[0]
    return None


def _install_wheel(path: str) -> None:
    # pip in the current interpreter covers pip --user and venv/pipx installs alike.
    proc = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", path],
                          capture_output=True, text=True)
    if proc.returncode == 0:
        return
    if shutil.which("pipx"):
        alt = subprocess.run(["pipx", "install", "--force", path], capture_output=True, text=True)
        if alt.returncode == 0:
            return
        raise ModricError(f"pipx upgrade failed: {alt.stderr.strip()[-400:]}")
    raise ModricError("upgrade failed: "
                      + (proc.stderr.strip()[-400:] or proc.stdout.strip()[-400:]))


def upgrade(target: str | None = None, check_only: bool = False) -> dict:
    current = __version__
    latest = target or latest_version()
    available = is_newer(latest, current) or (target is not None and target != current)
    if check_only:
        return {"current": current, "latest": latest, "upgrade_available": available}
    if not available:
        return {"current": current, "latest": latest, "upgraded": False,
                "message": "already up to date"}

    base = f"https://github.com/{_repo()}/releases/download/v{latest}"
    wheel = f"modric_cli-{latest}-py3-none-any.whl"
    blob = _get(f"{base}/{wheel}", accept="application/octet-stream")
    sums = _get(f"{base}/SHA256SUMS", accept="text/plain").decode("utf-8", "replace")
    expected = _expected_hash(sums, wheel)
    if expected and hashlib.sha256(blob).hexdigest() != expected:
        raise ModricError("checksum mismatch for the downloaded wheel — aborting upgrade")

    tmp = tempfile.mkdtemp()
    try:
        path = os.path.join(tmp, wheel)
        with open(path, "wb") as fh:
            fh.write(blob)
        _install_wheel(path)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return {"upgraded": True, "from": current, "to": latest}
