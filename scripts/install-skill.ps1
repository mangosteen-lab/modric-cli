# Install modric-cli as an agent skill on Windows.
#   powershell -ExecutionPolicy Bypass -File scripts\install-skill.ps1 [claude|codex|all]
param([string]$Target = "all")
$ErrorActionPreference = "Stop"
$RepoDir = Split-Path -Parent $PSScriptRoot

function Install-Claude {
    $home = if ($env:CLAUDE_HOME) { $env:CLAUDE_HOME } else { Join-Path $HOME ".claude" }
    $dest = Join-Path $home "skills\modric-troubleshooting"
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Copy-Item (Join-Path $RepoDir "skills\claude-code\SKILL.md") (Join-Path $dest "SKILL.md") -Force
    Write-Host "Claude Code skill installed -> $dest\SKILL.md"
}

function Install-Codex {
    $dir = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $agents = Join-Path $dir "AGENTS.md"
    if ((Test-Path $agents) -and (Select-String -Path $agents -SimpleMatch "<!-- modric-cli:begin -->")) {
        Write-Host "Codex snippet already present in $agents (skipping)"; return
    }
    $snippet = Get-Content (Join-Path $RepoDir "skills\codex\AGENTS-snippet.md") -Raw
    Add-Content $agents "`n<!-- modric-cli:begin -->`n$snippet`n<!-- modric-cli:end -->"
    Write-Host "Codex guidance appended -> $agents"
}

switch ($Target) {
    "claude" { Install-Claude }
    "codex"  { Install-Codex }
    "all"    { Install-Claude; Install-Codex }
    default  { Write-Error "usage: install-skill.ps1 [claude|codex|all]" }
}
