"""scripts: read / search / create / update / delete the user's scripts."""
from __future__ import annotations

from ..io_util import read_text
from ..search import Collector, compile_query, field_hit, grep
from ..session import make_client


def list_(args):
    return make_client(args).get("/api/scripts")


def get(args):
    return make_client(args).get(f"/api/scripts/{args.script_id}")


def create(args):
    body = {"path": args.path, "content": read_text(args.file, args.content)}
    if args.type is not None:
        body["script_type"] = args.type
    return make_client(args).post("/api/scripts", body)


def update(args):
    client = make_client(args)
    current = client.get(f"/api/scripts/{args.script_id}")
    body = {
        "path": args.path or current.get("path"),
        "content": read_text(args.file, args.content),
        "script_type": args.type if args.type is not None else current.get("script_type"),
    }
    return client.put(f"/api/scripts/{args.script_id}", body)


def delete(args):
    make_client(args).delete(f"/api/scripts/{args.script_id}")
    return {"deleted": True, "script_id": args.script_id}


def search(args):
    client = make_client(args)
    rx = compile_query(args.query, args.regex)
    col = Collector(args.limit)
    for s in client.get("/api/scripts"):
        if field_hit(s.get("path"), rx):
            col.add({"script_id": s["script_id"], "path": s["path"], "field": "path",
                     "snippet": s["path"]})
        if args.content and not col.full:
            full = client.get(f"/api/scripts/{s['script_id']}")
            for m in grep(full.get("content", ""), rx, args.before, args.after):
                col.add({"script_id": s["script_id"], "path": s["path"], "field": "content", **m})
                if col.full:
                    break
        if col.full:
            break
    return col.result()
