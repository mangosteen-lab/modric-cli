"""modric-cli — a zero-dependency command-line client for the Modric backend.

Designed so an external code agent (Claude Code, Codex, …) can read and author
Modric resources — scripts, job definitions, triggers, config-maps — and read job
execution records for troubleshooting, authenticating with the user's API token.
"""

try:
    from importlib.metadata import version as _dist_version

    __version__ = _dist_version("modric-cli")
except Exception:                       # running from source (not installed)
    __version__ = "0.0.3"
