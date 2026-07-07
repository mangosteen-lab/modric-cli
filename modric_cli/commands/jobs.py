"""jobs: read job execution records (for troubleshooting), read step logs, run, retry.

'jobs' are execution records — distinct from 'definitions' (the authorable templates).
"""
from __future__ import annotations

from ..io_util import parse_kv
from ..search import Collector, compile_query, field_hit, grep
from ..session import make_client


def list_(args):
    return make_client(args).get("/api/jobs", params={"definition_id": args.definition_id})


def get(args):
    return make_client(args).get(f"/api/jobs/{args.job_id}")


def logs(args):
    client = make_client(args)
    return client.get_text(
        f"/api/jobs/{args.job_id}/tasks/{args.step}/log", params={"tail": args.tail})


def run(args):
    body = {"job_definition_name": args.definition, "message": parse_kv(args.input),
            "dry_run": args.dry_run}
    return make_client(args).post("/api/jobs/run", body)


def retry(args):
    return make_client(args).post(f"/api/jobs/{args.job_id}/retry")


def search(args):
    """Search job execution records (any string field: name, status, error, ...)."""
    rx = compile_query(args.query, args.regex)
    col = Collector(args.limit)
    jobs = make_client(args).get("/api/jobs", params={"definition_id": args.definition_id})
    for job in jobs:
        if any(field_hit(v, rx) for v in job.values() if isinstance(v, str)):
            col.add(job)
        if col.full:
            break
    return col.result()


def search_logs(args):
    """Grep a job's step logs with context (all steps unless --step is given)."""
    client = make_client(args)
    rx = compile_query(args.query, args.regex)
    col = Collector(args.limit)
    job = client.get(f"/api/jobs/{args.job_id}")
    steps = [args.step] if args.step is not None else list(range(len(job.get("tasks", []))))
    for idx in steps:
        text = client.get_text(
            f"/api/jobs/{args.job_id}/tasks/{idx}/log", params={"tail": args.tail})
        for m in grep(text, rx, args.before, args.after):
            col.add({"step": idx, "line": m["line"], "snippet": m["snippet"]})
            if col.full:
                break
        if col.full:
            break
    return col.result()
