"""upgrade: self-update modric-cli from its GitHub releases (no Modric auth needed)."""
from __future__ import annotations

from ..updater import upgrade as _upgrade


def run(args):
    return _upgrade(target=args.version, check_only=args.check)
