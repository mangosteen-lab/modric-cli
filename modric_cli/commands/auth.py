"""auth: log in (save url + API token), show identity, log out."""
from __future__ import annotations

import getpass

from .. import config
from ..client import ModricClient
from ..session import make_client


def login(args):
    url = (args.url or config.load().get("url") or "").strip()
    if not url:
        url = input("Modric URL (e.g. https://modric.example.com): ").strip()
    token = (args.token or "").strip()
    if not token:
        token = getpass.getpass("Modric API token (from Account settings): ").strip()
    url = url.rstrip("/")
    me = ModricClient(url, token).get("/api/auth/me")   # validates before saving
    path = config.save(url, token)
    return {"logged_in": True, "url": url, "username": me.get("username"),
            "email": me.get("email"), "config": str(path)}


def whoami(args):
    me = make_client(args).get("/api/auth/me")
    return {"username": me.get("username"), "email": me.get("email"),
            "url": config.resolve(args.url, args.token)[0]}


def logout(args):
    path = config.config_path()
    existed = path.exists()
    if existed:
        path.unlink()
    return {"logged_out": True, "removed": existed, "config": str(path)}
