# Install modric-cli as an agent skill on Windows.
#
#   No clone:      irm https://raw.githubusercontent.com/mangosteen-lab/modric-cli/master/scripts/install-skill.ps1 | iex
#   From checkout: powershell -ExecutionPolicy Bypass -File scripts\install-skill.ps1 [claude|codex|all]
#
# Env: MODRIC_CLI_REPO, MODRIC_CLI_BRANCH (default: master).
param([string]$Target = "all")
$ErrorActionPreference = "Stop"
$repo = if ($env:MODRIC_CLI_REPO) { $env:MODRIC_CLI_REPO } else { "mangosteen-lab/modric-cli" }
$branch = if ($env:MODRIC_CLI_BRANCH) { $env:MODRIC_CLI_BRANCH } else { "master" }

$repoDir = $null
if ($PSScriptRoot -and (Test-Path (Join-Path $PSScriptRoot "..\pyproject.toml"))) {
    $repoDir = Split-Path -Parent $PSScriptRoot
}

function Fetch($relPath, $dest) {
    if ($repoDir) {
        Copy-Item (Join-Path $repoDir $relPath) $dest -Force
    } else {
        $url = "https://raw.githubusercontent.com/$repo/$branch/" + ($relPath -replace '\\', '/')
        Invoke-WebRequest $url -OutFile $dest
    }
}

function Install-Claude {
    $base = if ($env:CLAUDE_HOME) { $env:CLAUDE_HOME } else { Join-Path $HOME ".claude" }
    $dest = Join-Path $base "skills\modric-troubleshooting"
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Fetch "skills/claude-code/SKILL.md" (Join-Path $dest "SKILL.md")
    Write-Host "Claude Code skill installed -> $dest\SKILL.md"
}

function Install-Codex {
    $dir = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $agents = Join-Path $dir "AGENTS.md"
    if ((Test-Path $agents) -and (Select-String -Path $agents -SimpleMatch "<!-- modric-cli:begin -->")) {
        Write-Host "Codex snippet already present in $agents (skipping)"; return
    }
    $tmp = New-TemporaryFile
    Fetch "skills/codex/AGENTS-snippet.md" $tmp
    $snippet = Get-Content $tmp -Raw
    Remove-Item $tmp -Force
    Add-Content $agents "`n<!-- modric-cli:begin -->`n$snippet`n<!-- modric-cli:end -->"
    Write-Host "Codex guidance appended -> $agents"
}

switch ($Target) {
    "claude" { Install-Claude }
    "codex"  { Install-Codex }
    "all"    { Install-Claude; Install-Codex }
    default  { Write-Error "usage: install-skill.ps1 [claude|codex|all]" }
}
