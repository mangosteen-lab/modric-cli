"""definitions: read / create / update job definitions (the authorable 'jobs').

A definition's schema is rich (steps, machines, inputs, notification), so create/update
take a JSON document via --file. Use `definitions get <id>` to obtain a template to edit.
"""
from __future__ import annotations

from ..io_util import read_json
from ..search import Collector, compile_query, field_hit, grep
from ..session import make_client


def list_(args):
    return make_client(args).get("/api/definitions")


def get(args):
    return make_client(args).get(f"/api/definitions/{args.definition_id}")


def create(args):
    return make_client(args).post("/api/definitions", read_json(args.file))


def update(args):
    return make_client(args).put(f"/api/definitions/{args.definition_id}", read_json(args.file))


def delete(args):
    make_client(args).delete(f"/api/definitions/{args.definition_id}")
    return {"deleted": True, "definition_id": args.definition_id}


def search(args):
    client = make_client(args)
    rx = compile_query(args.query, args.regex)
    col = Collector(args.limit)
    for d in client.get("/api/definitions"):
        for field in ("name", "description"):
            if field_hit(d.get(field), rx):
                col.add({"definition_id": d["definition_id"], "name": d.get("name"),
                         "field": field, "snippet": str(d.get(field) or "")})
        if args.content and not col.full:
            full = client.get(f"/api/definitions/{d['definition_id']}")
            text = "\n".join(f"# step: {t.get('name', '')}\n{t.get('script_content', '')}"
                             for t in full.get("tasks", []))
            for m in grep(text, rx, args.before, args.after):
                col.add({"definition_id": d["definition_id"], "name": d.get("name"),
                         "field": "content", **m})
                if col.full:
                    break
        if col.full:
            break
    return col.result()
