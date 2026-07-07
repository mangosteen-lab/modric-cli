# Install the `modric` CLI on Windows.
#
#   No clone (recommended):
#     irm https://raw.githubusercontent.com/mangosteen-lab/modric-cli/master/scripts/install.ps1 | iex
#   From a checkout:
#     powershell -ExecutionPolicy Bypass -File scripts\install.ps1
#
# Env: MODRIC_CLI_VERSION (default: latest release), MODRIC_CLI_REPO, PYTHON.
$ErrorActionPreference = "Stop"
$repo = if ($env:MODRIC_CLI_REPO) { $env:MODRIC_CLI_REPO } else { "mangosteen-lab/modric-cli" }

function Install-Target($target) {
    if (Get-Command pipx -ErrorAction SilentlyContinue) {
        pipx install --force $target
    } else {
        $py = if ($env:PYTHON) { $env:PYTHON } else { "python" }
        & $py -m pip install --user --upgrade $target
        Write-Host "If 'modric' is missing, add (& $py -m site --user-base)\Scripts to PATH."
    }
}

# Local checkout?  (script in <repo>\scripts next to pyproject.toml)
$repoDir = $null
if ($PSScriptRoot -and (Test-Path (Join-Path $PSScriptRoot "..\pyproject.toml"))) {
    $repoDir = Split-Path -Parent $PSScriptRoot
}

if ($repoDir -and $env:MODRIC_CLI_FORCE_DOWNLOAD -ne "1") {
    Write-Host "Installing from local checkout ($repoDir)..."
    Install-Target $repoDir
} else {
    $version = $env:MODRIC_CLI_VERSION
    if (-not $version) {
        Write-Host "Resolving latest release of $repo..."
        $rel = Invoke-RestMethod "https://api.github.com/repos/$repo/releases/latest"
        $version = $rel.tag_name -replace '^v', ''
    }
    $tag = "v$version"
    $wheel = "modric_cli-$version-py3-none-any.whl"
    $base = "https://github.com/$repo/releases/download/$tag"
    $tmp = New-Item -ItemType Directory -Path (Join-Path $env:TEMP ([guid]::NewGuid()))
    try {
        Write-Host "Downloading $wheel ($tag)..."
        Invoke-WebRequest "$base/$wheel" -OutFile (Join-Path $tmp $wheel)
        Invoke-WebRequest "$base/SHA256SUMS" -OutFile (Join-Path $tmp "SHA256SUMS")
        $expected = (Select-String -Path (Join-Path $tmp "SHA256SUMS") -Pattern ([regex]::Escape($wheel)) |
                     ForEach-Object { ($_ -split '\s+')[0] } | Select-Object -First 1)
        $actual = (Get-FileHash (Join-Path $tmp $wheel) -Algorithm SHA256).Hash.ToLower()
        if (-not $expected -or $actual -ne $expected) { throw "checksum mismatch for $wheel" }
        Write-Host "Checksum OK. Installing..."
        Install-Target (Join-Path $tmp $wheel)
    } finally {
        Remove-Item -Recurse -Force $tmp
    }
}

Write-Host ""
Write-Host "Installed. Next:"
Write-Host "  modric auth login --url https://your-modric-host --token <API_TOKEN>"
Write-Host "  modric --help"
