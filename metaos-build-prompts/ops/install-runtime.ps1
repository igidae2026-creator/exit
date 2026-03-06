[CmdletBinding()]
param(
    [string]$EnvFile,
    [switch]$SkipPip
)

$ErrorActionPreference = 'Stop'

function Import-MetaOSEnv {
    param([string]$FilePath)

    if (-not (Test-Path -LiteralPath $FilePath)) {
        throw "Env file not found: $FilePath"
    }

    Get-Content -LiteralPath $FilePath | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith('#')) { return }

        $parts = $line.Split('=', 2)
        if ($parts.Count -ne 2) { return }

        $key = $parts[0].Trim()
        $val = $parts[1].Trim().Trim('"').Trim("'")
        Set-Item -Path "env:$key" -Value $val
    }
}

$envPath = if ($EnvFile) { $EnvFile } else { Join-Path $PSScriptRoot 'METAOS.env' }
Import-MetaOSEnv -FilePath $envPath

$rootRel = if ($env:METAOS_ROOT) { $env:METAOS_ROOT } else { '..' }
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot $rootRel)
$python = if ($env:METAOS_PYTHON) { $env:METAOS_PYTHON } else { 'python' }

if (-not (Get-Command $python -ErrorAction SilentlyContinue)) {
    throw "Python command not found: $python"
}

$versionOutput = & $python --version 2>&1
Write-Host "Detected runtime: $versionOutput"
if ($versionOutput -notmatch '3\.11\.') {
    Write-Warning 'METAOS recommends Python 3.11.x'
}

if ($SkipPip) {
    exit 0
}

$requirements = Join-Path $repoRoot 'requirements.txt'
if (Test-Path -LiteralPath $requirements) {
    Write-Host 'Installing Python dependencies from requirements.txt...'
    & $python -m pip install -r $requirements
}
else {
    Write-Host 'No requirements.txt found. Skipping pip install.'
}
