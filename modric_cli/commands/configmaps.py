"""configmaps: read / create / update config-maps. Secret VALUES are never returned by
the API (only keys + has_value), and update preserves existing secrets you don't resupply.
"""
from __future__ import annotations

from ..client import ModricError
from ..io_util import parse_kv
from ..search import Collector, compile_query, field_hit
from ..session import make_client


def _by_name(client, name):
    for cm in client.get("/api/configmaps"):
        if cm["name"] == name:
            return cm
    raise ModricError(f"config map '{name}' not found")


def list_(args):
    return make_client(args).get("/api/configmaps")


def get(args):
    return _by_name(make_client(args), args.name)


def _entries(keys, secrets):
    out = [{"key": k, "value": v, "sensitive": False} for k, v in parse_kv(keys).items()]
    out += [{"key": k, "value": v, "sensitive": True} for k, v in parse_kv(secrets).items()]
    return out


def create(args):
    body = {"name": args.name, "description": args.description or "",
            "entries": _entries(args.key, args.secret)}
    return make_client(args).post("/api/configmaps", body)


def update(args):
    client = make_client(args)
    cm = _by_name(client, args.name)
    # Start from the current (masked) entries so unspecified keys are kept. Masked
    # secrets come back with value="" + sensitive=true, which the server preserves.
    by_key = {e["key"]: {"key": e["key"], "value": e["value"], "sensitive": e["sensitive"]}
              for e in cm["entries"]}
    for entry in _entries(args.key, args.secret):
        by_key[entry["key"]] = entry
    for key in (args.remove or []):
        by_key.pop(key, None)
    body = {"name": cm["name"],
            "description": args.description if args.description is not None else cm["description"],
            "entries": list(by_key.values())}
    return client.put(f"/api/configmaps/{cm['config_map_id']}", body)


def delete(args):
    client = make_client(args)
    cm = _by_name(client, args.name)
    client.delete(f"/api/configmaps/{cm['config_map_id']}")
    return {"deleted": True, "name": args.name, "config_map_id": cm["config_map_id"]}


def search(args):
    # Never searches secret VALUES (the API doesn't return them) — only names,
    # descriptions and keys.
    rx = compile_query(args.query, args.regex)
    col = Collector(args.limit)
    for cm in make_client(args).get("/api/configmaps"):
        for field in ("name", "description"):
            if field_hit(cm.get(field), rx):
                col.add({"config_map_id": cm["config_map_id"], "name": cm["name"],
                         "field": field, "snippet": str(cm.get(field) or "")})
        for entry in cm.get("entries", []):
            if field_hit(entry.get("key"), rx):
                col.add({"config_map_id": cm["config_map_id"], "name": cm["name"],
                         "field": "key", "snippet": entry["key"]})
            if col.full:
                break
        if col.full:
            break
    return col.result()
