"""Build an authenticated client from CLI flags / env / config file."""
from __future__ import annotations

from . import config
from .client import ModricClient


def make_client(args) -> ModricClient:
    url, token = config.resolve(getattr(args, "url", None), getattr(args, "token", None))
    return ModricClient(url, token)
