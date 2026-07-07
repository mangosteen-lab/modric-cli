# modric-cli

A small, **zero-dependency** command-line client for the [Modric](https://github.com/mangosteen-lab/modric)
CI/orchestration backend. It's built so an **external code agent** (Claude Code, Codex,
opencode, …) can:

- **read / create / update** scripts, job definitions, triggers, and config-maps
  (config-map **secret values are never exposed** — only keys), and
- **read job execution records** (status, per-step logs, runtime state) to troubleshoot failures.

You put your Modric API token in the CLI config once; the agent then drives `modric` to
investigate and fix jobs on your behalf.

> Modric terminology: a **definition** is an authorable job template; a **job** is one
> execution record of a definition. Scripts, triggers, and config-maps are shared resources.

## Install

Requires Python 3.9+. No other runtime dependencies. **No clone needed** — the install
script downloads the released wheel from GitHub and verifies its checksum.

**macOS / Linux**
```bash
curl -fsSL https://raw.githubusercontent.com/mangosteen-lab/modric-cli/master/scripts/install.sh | sh
```

**Windows (PowerShell)**
```powershell
irm https://raw.githubusercontent.com/mangosteen-lab/modric-cli/master/scripts/install.ps1 | iex
```

Pin a version with `MODRIC_CLI_VERSION=0.0.1` before the command. From a checkout you can
also run `make install` (installs the local source). Verify with `modric --help`.

## Authenticate

Get your API token from the Modric web UI → **Account settings**, then:

```bash
modric auth login --url https://your-modric-host --token <API_TOKEN>
modric auth whoami
```

Credentials are saved to `~/.config/modric/config.json` (Linux/macOS) or
`%APPDATA%\modric\config.json` (Windows), `chmod 600`. You can instead export
`MODRIC_URL` and `MODRIC_TOKEN`, or pass `--url` / `--token` on any command.
Precedence: **flag > env > config file**.

## Install as an agent skill

Teach Claude Code / Codex to use this CLI automatically — also **no clone needed**:

```bash
curl -fsSL https://raw.githubusercontent.com/mangosteen-lab/modric-cli/master/scripts/install-skill.sh | sh -s -- all
```
Pass `claude` or `codex` instead of `all` for just one. Windows:
```powershell
irm https://raw.githubusercontent.com/mangosteen-lab/modric-cli/master/scripts/install-skill.ps1 | iex
```
From a checkout: `make install-skill`. Remove with `make uninstall-skill` (or
`scripts/uninstall-skill.sh all`). Claude Code lands in
`~/.claude/skills/modric-troubleshooting/`; Codex appends to `~/.codex/AGENTS.md`.

## Command reference

Every command prints **JSON** by default (ideal for agents). Add `--table` to a `list` for a
human-readable grid. Get help anywhere with `modric <resource> [<action>] --help`.

### Troubleshoot a failed job (the main workflow)

```bash
# From a job link https://host/#view?job=JOB_ID, take JOB_ID:
modric jobs get JOB_ID                 # status, error, per-step status, runtime state, inputs
modric jobs logs JOB_ID --step 2       # tail of step 2's log (default step 0, --tail bytes)
modric definitions get DEF_ID          # the definition behind the job
modric scripts get SCRIPT_ID           # a step's script
```

### Search (all resources + logs)

Every resource has a `search` subcommand, plus `jobs search-logs` for step logs. Shared flags:

- `--regex` — treat the query as a regular expression (default: case-insensitive substring)
- `-B N` / `--before N`, `-A N` / `--after N` — context lines around each **content/log** match
- `--limit N` — cap results (hard maximum **1000**)

**Hard output caps** (so an agent never pulls too much): at most **1000 results**, and each
result's text is truncated to **10 KB**. The response is `{returned, truncated, limit, results}`.

```bash
modric scripts search deploy                     # match script paths
modric scripts search "rm -rf" --content -B 2 -A 2   # grep content, 2 lines of context
modric definitions search nightly --content      # names/descriptions + step scripts
modric triggers search "0 3"                      # names/descriptions/cron
modric configmaps search TOKEN                    # names/descriptions/keys (never secret values)
modric jobs search FAILED                         # execution records by any field
modric jobs search-logs JOB_ID "error|traceback" --regex -B 3 -A 3   # all steps' logs
modric jobs search-logs JOB_ID "npm" --step 1     # one step only
```

### scripts
```bash
modric scripts list
modric scripts get SCRIPT_ID
modric scripts search QUERY [--content] [-B N] [-A N]
modric scripts create --path scripts/sh/deploy.sh --file ./deploy.sh --type 3
echo 'echo hi' | modric scripts create --path scripts/sh/hi.sh --file - --type 3
modric scripts update SCRIPT_ID --content 'echo fixed'
modric scripts delete SCRIPT_ID --yes
```
Script types: `1=bat 2=python 3=shell 4=powershell 5=node 6=ruby 7=perl 8=go 9=auto`.

### definitions (authorable jobs)
```bash
modric definitions list
modric definitions get DEF_ID > def.json     # use as an edit template
modric definitions search QUERY [--content]
modric definitions create --file def.json
modric definitions update DEF_ID --file def.json
modric definitions delete DEF_ID --yes
```

### jobs (execution records)
```bash
modric jobs list [--definition-id DEF_ID]
modric jobs get JOB_ID
modric jobs logs JOB_ID --step 0 --tail 65536
modric jobs search QUERY [--definition-id DEF_ID]      # search execution records
modric jobs search-logs JOB_ID QUERY [--step N] [-B N] [-A N]
modric jobs run --definition "Nightly Build" --input BRANCH=main --input ENV=stage
modric jobs retry JOB_ID
```
(Job execution records cannot be deleted via the API.)

### triggers
```bash
modric triggers list
modric triggers search QUERY
modric triggers create --name nightly --cron "0 3 * * *" --description "3am UTC"
modric triggers update TRIGGER_ID --cron "30 2 * * *"
modric triggers delete TRIGGER_ID --yes
```

### configmaps (secret values never returned)
```bash
modric configmaps list
modric configmaps get creds                       # values masked; keys + has_value only
modric configmaps search QUERY                     # names/descriptions/keys (never values)
modric configmaps create creds --key REGION=us --secret TOKEN=s3cr3t
modric configmaps update creds --key REGION=eu    # other keys (incl. secrets) preserved
modric configmaps update creds --remove OLD_KEY
modric configmaps delete creds --yes
```
`update` keeps existing keys you don't mention; a secret you don't resupply is preserved
(the API returns masked secrets, and the server keeps the stored value).

**Deletes** require `-y`/`--yes` when run non-interactively (agents must pass it explicitly);
interactively they prompt for confirmation.

## End-to-end example (agent troubleshooting)

```bash
$ modric jobs get 8e84efd4-...        # -> step "build" is FAILED, error "npm: not found"
$ modric jobs logs 8e84efd4-... --step 1
...
npm: command not found
$ modric scripts get 5b6890c3-...     # inspect the build script
# fix: switch the step to install node first, or run on a node-capable machine, then:
$ modric jobs retry 8e84efd4-...
```

## Copy-prompt from the web UI

The Modric job page has a **"Copy troubleshooting prompt"** button that copies:

> This is a Modric job execution record, link: `<link>`. Please help me troubleshoot the
> issue with modric-cli.

Paste that into your code agent (with this CLI installed as a skill) and it will investigate
using the commands above.

## Development

```bash
make test      # pytest (fakes the network — no live backend needed)
make lint      # ruff
make build     # sdist + wheel into dist/
```

## License

MIT — see [LICENSE](LICENSE).
