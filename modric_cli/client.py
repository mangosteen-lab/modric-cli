"""Thin HTTP client for the Modric REST API — standard library only.

Authenticates every request with the `X-Api-Token` header (the user's Modric API
token). Raises ModricError on transport failures and non-2xx responses, carrying the
server's error detail so the CLI can print something actionable.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request


class ModricError(Exception):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


class ModricClient:
    def __init__(self, url: str, token: str, timeout: int = 60):
        _hint = "Run: modric auth login --url <url> --token <token>"
        if not url:
            raise ModricError(f"No Modric URL configured. {_hint}")
        if not token:
            raise ModricError(f"No API token configured. {_hint}")
        self.url = url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def request(self, method: str, path: str, body=None, params: dict | None = None):
        target = self.url + path
        if params:
            clean = {k: v for k, v in params.items() if v is not None}
            if clean:
                target += "?" + urllib.parse.urlencode(clean)
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(target, data=data, method=method)
        req.add_header("X-Api-Token", self.token)
        req.add_header("Accept", "application/json")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as exc:
            raise ModricError(_error_detail(exc), status=exc.code) from exc
        except urllib.error.URLError as exc:
            raise ModricError(f"Cannot reach Modric at {self.url}: {exc.reason}") from exc
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw.decode("utf-8", "replace")

    def get(self, path, params=None):
        return self.request("GET", path, params=params)

    def post(self, path, body=None):
        return self.request("POST", path, body=body)

    def put(self, path, body=None):
        return self.request("PUT", path, body=body)

    def delete(self, path):
        return self.request("DELETE", path)

    def get_text(self, path, params=None):
        """GET a plain-text endpoint (e.g. step logs) as a decoded string."""
        out = self.request("GET", path, params=params)
        return out if isinstance(out, str) else json.dumps(out, indent=2)


def _error_detail(exc: urllib.error.HTTPError) -> str:
    try:
        payload = json.loads(exc.read())
        detail = payload.get("detail") if isinstance(payload, dict) else None
        if detail:
            return f"{exc.code} {detail}"
    except Exception:
        pass
    return f"HTTP {exc.code} {exc.reason}"
