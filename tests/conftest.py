"""Test fixtures: an in-memory fake of urllib so the client stack runs without network."""
import io
import json
import urllib.error
import urllib.request

import pytest


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


class FakeServer:
    """Records requests and returns canned responses keyed by 'METHOD /path'."""
    def __init__(self):
        self.routes = {}
        self.calls = []

    def route(self, method, path, response=None, status=200):
        self.routes[f"{method} {path}"] = (status, response)

    def _handle(self, req, timeout=None):
        method = req.get_method()
        full = req.full_url
        path = full.split("://", 1)[-1].split("/", 1)[-1]
        path = "/" + path.split("?", 1)[0]
        body = json.loads(req.data.decode()) if req.data else None
        self.calls.append({"method": method, "path": path, "body": body,
                           "headers": dict(req.header_items())})
        status, response = self.routes.get(f"{method} {path}", (200, {}))
        if status >= 400:
            raise urllib.error.HTTPError(full, status, "err", {},
                                         io.BytesIO(json.dumps(response or {}).encode()))
        payload = response if isinstance(response, (bytes, str)) else json.dumps(response or {})
        return FakeResp(payload.encode() if isinstance(payload, str) else payload)


@pytest.fixture
def server(monkeypatch, tmp_path):
    srv = FakeServer()
    monkeypatch.setattr(urllib.request, "urlopen", srv._handle)
    monkeypatch.setenv("MODRIC_URL", "https://modric.test")
    monkeypatch.setenv("MODRIC_TOKEN", "tok-123")
    monkeypatch.setenv("MODRIC_CONFIG", str(tmp_path / "config.json"))
    return srv
