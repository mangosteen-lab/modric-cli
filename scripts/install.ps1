# Install the `modric` CLI on Windows. Prefers pipx, falls back to pip --user.
# Run from the repo root:  powershell -ExecutionPolicy Bypass -File scripts\install.ps1
$ErrorActionPreference = "Stop"
$RepoDir = Split-Path -Parent $PSScriptRoot
Set-Location $RepoDir

if (Get-Command pipx -ErrorAction SilentlyContinue) {
    Write-Host "Installing with pipx..."
    pipx install --force .
} else {
    $py = if ($env:PYTHON) { $env:PYTHON } else { "python" }
    Write-Host "pipx not found; installing with $py -m pip install --user ..."
    & $py -m pip install --user --upgrade .
    Write-Host ""
    Write-Host "If 'modric' is not found, add your user Scripts dir to PATH:"
    Write-Host "  `$env:Path += ';' + (& $py -m site --user-base) + '\Scripts'"
}

Write-Host ""
Write-Host "Installed. Next:"
Write-Host "  modric auth login --url https://your-modric-host --token <API_TOKEN>"
Write-Host "  modric --help"
