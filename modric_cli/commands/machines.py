"""machine: list registered machines, get one by id, and run a command on it via its agent."""
from __future__ import annotations

from ..io_util import read_text
from ..session import make_client


def list_(args):
    return make_client(args).get("/api/machines")


def get(args):
    return make_client(args).get(f"/api/machines/{args.machine_id}")


def run(args):
    body = {"command": read_text(args.file, args.command),
            "script_type": args.type, "timeout": args.timeout}
    if args.arg:
        body["args"] = args.arg
    return make_client(args).post(f"/api/machines/{args.machine_id}/run", body)
