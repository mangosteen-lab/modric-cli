---
name: modric-troubleshooting
description: >-
  Use when the user asks to troubleshoot a Modric job execution, or to read/create/update
  Modric scripts, job definitions, triggers, or config-maps. Triggers on a Modric job
  execution link (contains "#view?job="), a job id, or phrases like "modric job failed",
  "troubleshoot with modric-cli", "modric script/trigger/config-map". Drives the `modric` CLI.
---

# Modric troubleshooting & authoring via `modric-cli`

The `modric` command is a CLI onto the Modric CI/orchestration backend. Use it to inspect
job execution records and to read/create/update resources. It authenticates with the
credentials saved by `modric auth login` (or `MODRIC_URL` / `MODRIC_TOKEN` env vars).

**Prerequisite:** `modric --help` should work. If it errors with "No API token configured",
ask the user to run `modric auth login --url <host> --token <API_TOKEN>` (token is in the
Modric web UI under Account settings). Never ask the user to paste the token to you.

Every command prints JSON by default — parse it directly.

## Troubleshooting a failed job (primary workflow)

Given a job execution link like `https://host/#view?job=<JOB_ID>`, extract `<JOB_ID>`, then:

```bash
modric jobs get <JOB_ID>                 # status, error, per-step status, runtime state, inputs
modric jobs logs <JOB_ID> --step <N>     # tail of a FAILED step's log (default step 0)
```

1. `modric jobs get <JOB_ID>` — find the step whose status is `FAILED` and read `error`.
2. `modric jobs logs <JOB_ID> --step <N>` for that step — read the tail for the real error.
3. Inspect the resource behind the step: `modric scripts get <id>` /
   `modric definitions get <id>` / `modric configmaps get <name>` (secret values are never
   shown — only keys).
4. Propose a fix. With the user's go-ahead, apply it (`scripts update`, `configmaps update`,
   `definitions update`) and re-run: `modric jobs run --definition "<name>"` then
   `modric jobs get <new_job_id>`.

## Resource commands

```bash
modric scripts list | get <id> | create --path P --file F --type N | update <id> --file F | delete <id> --yes
modric definitions list | get <id> | create --file def.json | update <id> --file def.json | delete <id> --yes
modric triggers list | create --name N --cron "0 3 * * *" | update <id> --cron "..." | delete <id> --yes
modric configmaps list | get <name> | create <name> --key K=V --secret K=V | update <name> --key K=V | delete <name> --yes
modric jobs list [--definition-id ID] | get <id> | logs <id> --step N | run --definition NAME --input K=V | retry <id>
modric machine list | get <id> | run <id> "<command>" [--type N] [--timeout S]
```

`modric machine run` executes a command on a machine's agent and returns
`{status, exit_code, output}` — use it while troubleshooting to inspect the box that ran a
failed job (check a dependency, env var, path, or disk). `--type` defaults to 9 (auto: cmd on
Windows, bash on Linux).

Script types: `1=bat 2=python 3=shell 4=powershell 5=node 6=ruby 7=perl 8=go 9=auto`.

## Search (find things without pulling too much)

Every resource has `search`, plus `jobs search-logs` for step logs. Shared flags: `--regex`,
`-B N` / `-A N` (context lines before/after each content/log match), `--limit N`. Results are
**hard-capped at 1000**, each result's text at **10 KB** — prefer a specific query with small
`-B`/`-A` over reading whole scripts or logs.

```bash
modric jobs search-logs <JOB_ID> "error|traceback|fatal" --regex -B 3 -A 3   # find the error fast
modric scripts search "<term>" --content -B 2 -A 2      # grep script content with context
modric definitions search "<term>" --content
modric triggers search "<term>"       # name/description/cron
modric configmaps search "<term>"     # name/description/keys (never secret values)
modric jobs search FAILED             # execution records by any field
```

## Rules

- **Secrets:** config-map values are never returned by the API. Do not ask the user for
  secret values unless they explicitly want to set one via `--secret KEY=VALUE`.
- **Confirm writes:** before any `create`/`update`/`run`, show the user what you will do and
  wait for confirmation. Reads (`list`/`get`/`logs`/`search`) need no confirmation.
- **Delete is destructive:** only `delete` with the user's explicit go-ahead; it requires
  `--yes`. Never delete speculatively.
- Use `--json` output as-is; add `--table` only when presenting a list to a human.
- Full command help: `modric <resource> --help`.
