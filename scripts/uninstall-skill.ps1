# Remove the modric-cli agent skill on Windows.
#   powershell -ExecutionPolicy Bypass -File scripts\uninstall-skill.ps1 [claude|codex|all]
param([string]$Target = "all")
$ErrorActionPreference = "Stop"

function Remove-Claude {
    $home = if ($env:CLAUDE_HOME) { $env:CLAUDE_HOME } else { Join-Path $HOME ".claude" }
    $dest = Join-Path $home "skills\modric-troubleshooting"
    if (Test-Path $dest) { Remove-Item -Recurse -Force $dest; Write-Host "Removed $dest" }
}

function Remove-Codex {
    $dir = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
    $agents = Join-Path $dir "AGENTS.md"
    if (-not (Test-Path $agents)) { return }
    $text = Get-Content $agents -Raw
    $text = [regex]::Replace($text, "(?s)\s*<!-- modric-cli:begin -->.*?<!-- modric-cli:end -->", "")
    Set-Content $agents $text
    Write-Host "Removed Codex snippet from $agents"
}

switch ($Target) {
    "claude" { Remove-Claude }
    "codex"  { Remove-Codex }
    "all"    { Remove-Claude; Remove-Codex }
    default  { Write-Error "usage: uninstall-skill.ps1 [claude|codex|all]" }
}
