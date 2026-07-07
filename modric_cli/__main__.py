"""modric — command-line client for the Modric backend.

Usage: modric <resource> <action> [options]
Resources: auth, scripts, definitions, jobs, triggers, configmaps.
Global options (--url/--token/--table) work after any subcommand.
"""
from __future__ import annotations

import argparse
import sys

from . import __version__
from .client import ModricError
from .commands import auth, configmaps, definitions, jobs, scripts, triggers
from .output import die, emit


def _common() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--url", help="Modric base URL (overrides config/env)")
    p.add_argument("--token", help="API token (overrides config/env)")
    p.add_argument("--table", action="store_true", help="render list results as a table")
    return p


def _search_flags() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--regex", action="store_true", help="treat the query as a regex")
    p.add_argument("-B", "--before", type=int, default=0, metavar="N",
                   help="context lines before each content/log match")
    p.add_argument("-A", "--after", type=int, default=0, metavar="N",
                   help="context lines after each content/log match")
    p.add_argument("--limit", type=int, default=1000,
                   help="max results (hard cap 1000); each result's text is capped at 10 KB")
    return p


def _confirm_flag() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("-y", "--yes", action="store_true", help="skip the delete confirmation prompt")
    return p


def build_parser() -> argparse.ArgumentParser:
    common = _common()
    sflags = _search_flags()
    yesf = _confirm_flag()
    parser = argparse.ArgumentParser(prog="modric", parents=[common],
                                     description="Modric CLI for scripts, jobs, triggers, "
                                                 "config-maps, and job execution records.")
    parser.add_argument("--version", action="version", version=f"modric-cli {__version__}")
    res = parser.add_subparsers(dest="resource", required=True)

    def leaf(sub, name, handler, help_, extra=()):
        s = sub.add_parser(name, parents=[common, *extra], help=help_)
        s.set_defaults(handler=handler)
        return s

    def delete_leaf(sub, name, handler, help_):
        s = leaf(sub, name, handler, help_, extra=[yesf])
        s.set_defaults(destructive=True)
        return s

    # auth ------------------------------------------------------------------
    a = res.add_parser("auth", help="authenticate and manage the saved credentials")
    asub = a.add_subparsers(dest="action", required=True)
    leaf(asub, "login", auth.login, "save the Modric URL + API token to the config file")
    leaf(asub, "whoami", auth.whoami, "show the authenticated user")
    leaf(asub, "logout", auth.logout, "remove the saved credentials")

    # scripts ---------------------------------------------------------------
    sc = res.add_parser("scripts", help="read / create / update scripts")
    scsub = sc.add_subparsers(dest="action", required=True)
    leaf(scsub, "list", scripts.list_, "list scripts")
    g = leaf(scsub, "get", scripts.get, "get a script by id")
    g.add_argument("script_id")
    c = leaf(scsub, "create", scripts.create, "create a script")
    c.add_argument("--path", required=True, help="repo-relative path, e.g. scripts/sh/x.sh")
    c.add_argument("--file", help="read content from a file ('-' for stdin)")
    c.add_argument("--content", help="inline content (overrides --file)")
    c.add_argument("--type", type=int, help="1=bat 2=python 3=shell 4=powershell 5=node "
                                            "6=ruby 7=perl 8=go 9=auto")
    u = leaf(scsub, "update", scripts.update, "replace a script's content")
    u.add_argument("script_id")
    u.add_argument("--file", help="read content from a file ('-' for stdin)")
    u.add_argument("--content", help="inline content (overrides --file)")
    u.add_argument("--path", help="new path (kept if omitted)")
    u.add_argument("--type", type=int, help="new script type (kept if omitted)")
    d = delete_leaf(scsub, "delete", scripts.delete, "delete a script")
    d.add_argument("script_id")
    s = leaf(scsub, "search", scripts.search, "search scripts by path (and --content)",
             extra=[sflags])
    s.add_argument("query")
    s.add_argument("--content", action="store_true",
                   help="also grep script content (extra fetches)")

    # definitions -----------------------------------------------------------
    d = res.add_parser("definitions", aliases=["def"],
                       help="read / create / update job definitions")
    dsub = d.add_subparsers(dest="action", required=True)
    leaf(dsub, "list", definitions.list_, "list definitions")
    g = leaf(dsub, "get", definitions.get, "get a definition by id (use as an edit template)")
    g.add_argument("definition_id")
    c = leaf(dsub, "create", definitions.create, "create a definition from a JSON file")
    c.add_argument("--file", required=True, help="JSON document ('-' for stdin)")
    u = leaf(dsub, "update", definitions.update, "update a definition from a JSON file")
    u.add_argument("definition_id")
    u.add_argument("--file", required=True, help="JSON document ('-' for stdin)")
    dl = delete_leaf(dsub, "delete", definitions.delete, "delete a definition")
    dl.add_argument("definition_id")
    s = leaf(dsub, "search", definitions.search, "search definitions by name/description/content",
             extra=[sflags])
    s.add_argument("query")
    s.add_argument("--content", action="store_true", help="also grep step script content")

    # jobs (execution records) ---------------------------------------------
    j = res.add_parser("jobs", help="read job execution records (troubleshooting), run, retry")
    jsub = j.add_subparsers(dest="action", required=True)
    ls = leaf(jsub, "list", jobs.list_, "list recent job executions")
    ls.add_argument("--definition-id", dest="definition_id", help="filter by definition")
    g = leaf(jsub, "get", jobs.get, "get a job execution record (status, steps, error, state)")
    g.add_argument("job_id")
    lg = leaf(jsub, "logs", jobs.logs, "read a step's log tail")
    lg.add_argument("job_id")
    lg.add_argument("--step", type=int, default=0, help="step (task) index, default 0")
    lg.add_argument("--tail", type=int, default=100 * 1024, help="tail bytes, default 100 KB")
    r = leaf(jsub, "run", jobs.run, "launch a job from a definition")
    r.add_argument("--definition", required=True, help="definition name to run")
    r.add_argument("--input", action="append", metavar="KEY=VALUE", help="repeatable input")
    r.add_argument("--dry-run", dest="dry_run", action="store_true", help="render without running")
    rt = leaf(jsub, "retry", jobs.retry, "retry a failed job from its first failed step")
    rt.add_argument("job_id")
    js = leaf(jsub, "search", jobs.search, "search job execution records (name/status/error/...)",
              extra=[sflags])
    js.add_argument("query")
    js.add_argument("--definition-id", dest="definition_id", help="filter by definition")
    sl = leaf(jsub, "search-logs", jobs.search_logs, "grep a job's step logs with context",
              extra=[sflags])
    sl.add_argument("job_id")
    sl.add_argument("query")
    sl.add_argument("--step", type=int, help="a single step index (default: all steps)")
    sl.add_argument("--tail", type=int, default=1024 * 1024,
                    help="max log bytes per step to search, default 1 MB")

    # triggers --------------------------------------------------------------
    t = res.add_parser("triggers", help="read / create / update cron triggers")
    tsub = t.add_subparsers(dest="action", required=True)
    leaf(tsub, "list", triggers.list_, "list triggers")
    c = leaf(tsub, "create", triggers.create, "create a cron trigger")
    c.add_argument("--name", required=True)
    c.add_argument("--cron", required=True, help="5-field cron expression (UTC)")
    c.add_argument("--description")
    u = leaf(tsub, "update", triggers.update, "update a cron trigger")
    u.add_argument("trigger_id")
    u.add_argument("--name")
    u.add_argument("--cron")
    u.add_argument("--description")
    dl = delete_leaf(tsub, "delete", triggers.delete, "delete a trigger")
    dl.add_argument("trigger_id")
    s = leaf(tsub, "search", triggers.search, "search triggers by name/description/cron",
             extra=[sflags])
    s.add_argument("query")

    # configmaps ------------------------------------------------------------
    cm = res.add_parser("configmaps", aliases=["cm"], help="read / create / update config-maps "
                                                           "(secret values never exposed)")
    cmsub = cm.add_subparsers(dest="action", required=True)
    leaf(cmsub, "list", configmaps.list_, "list config-maps (keys + has_value, no secret values)")
    g = leaf(cmsub, "get", configmaps.get, "get a config-map by name (values masked)")
    g.add_argument("name")
    c = leaf(cmsub, "create", configmaps.create, "create a config-map")
    c.add_argument("name")
    c.add_argument("--key", action="append", metavar="KEY=VALUE", help="non-secret entry")
    c.add_argument("--secret", action="append", metavar="KEY=VALUE", help="secret entry")
    c.add_argument("--description")
    u = leaf(cmsub, "update", configmaps.update, "add/update keys (unspecified keys kept)")
    u.add_argument("name")
    u.add_argument("--key", action="append", metavar="KEY=VALUE", help="non-secret entry")
    u.add_argument("--secret", action="append", metavar="KEY=VALUE", help="secret entry")
    u.add_argument("--remove", action="append", metavar="KEY", help="remove a key")
    u.add_argument("--description")
    dl = delete_leaf(cmsub, "delete", configmaps.delete, "delete a config-map")
    dl.add_argument("name")
    s = leaf(cmsub, "search", configmaps.search,
             "search config-maps by name/description/key (never secret values)", extra=[sflags])
    s.add_argument("query")

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "handler", None):
        parser.print_help()
        return 2
    if getattr(args, "destructive", False) and not getattr(args, "yes", False):
        if not sys.stdin.isatty():
            die("refusing to delete without --yes in a non-interactive session")
        if input("This permanently deletes the resource. Continue? [y/N] ").strip().lower() \
                not in ("y", "yes"):
            print("aborted")
            return 1
    try:
        result = args.handler(args)
    except ModricError as exc:
        die(str(exc))
    except KeyboardInterrupt:
        return 130
    emit(result, as_json=not getattr(args, "table", False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
