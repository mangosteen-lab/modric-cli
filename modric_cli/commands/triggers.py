"""triggers: read / search / create / update / delete reusable cron triggers."""
from __future__ import annotations

from ..search import Collector, compile_query, field_hit
from ..session import make_client


def list_(args):
    return make_client(args).get("/api/triggers")


def create(args):
    return make_client(args).post(
        "/api/triggers",
        {"name": args.name, "cron": args.cron, "description": args.description or ""})


def update(args):
    client = make_client(args)
    current = {t["trigger_id"]: t for t in client.get("/api/triggers")}.get(args.trigger_id, {})
    body = {"name": args.name or current.get("name"),
            "cron": args.cron or current.get("cron"),
            "description": args.description if args.description is not None
            else current.get("description", "")}
    return client.put(f"/api/triggers/{args.trigger_id}", body)


def delete(args):
    make_client(args).delete(f"/api/triggers/{args.trigger_id}")
    return {"deleted": True, "trigger_id": args.trigger_id}


def search(args):
    rx = compile_query(args.query, args.regex)
    col = Collector(args.limit)
    for t in make_client(args).get("/api/triggers"):
        for field in ("name", "description", "cron"):
            if field_hit(t.get(field), rx):
                col.add({"trigger_id": t["trigger_id"], "name": t.get("name"),
                         "field": field, "snippet": str(t.get(field) or "")})
        if col.full:
            break
    return col.result()
