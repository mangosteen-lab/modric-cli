# Uninstall the `modric` CLI on Windows.
$ErrorActionPreference = "Stop"
if ((Get-Command pipx -ErrorAction SilentlyContinue) -and (pipx list | Select-String "modric-cli")) {
    pipx uninstall modric-cli
} else {
    $py = if ($env:PYTHON) { $env:PYTHON } else { "python" }
    & $py -m pip uninstall -y modric-cli
}
Write-Host "Removed the 'modric' command. (Config at %APPDATA%\modric\config.json is left in place.)"
