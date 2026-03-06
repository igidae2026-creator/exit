[CmdletBinding()]
param(
    [string]$Instance,
    [string]$EnvFile,
    [switch]$NoRestart
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

if (-not $Instance) {
    $Instance = if ($env:METAOS_INSTANCE_ID) { $env:METAOS_INSTANCE_ID } else { 'default' }
}

$rootRel = if ($env:METAOS_ROOT) { $env:METAOS_ROOT } else { '..' }
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot $rootRel)
$instancesDirName = if ($env:METAOS_INSTANCES_DIR) { $env:METAOS_INSTANCES_DIR } else { 'instances' }
$instancesRoot = Join-Path $repoRoot $instancesDirName
$instanceDir = Join-Path $instancesRoot $Instance
$archiveRoot = Join-Path $instancesRoot '_archive'
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$archivedName = "{0}-{1}" -f $Instance, $timestamp
$archivedDir = Join-Path $archiveRoot $archivedName

if (Test-Path -LiteralPath $instanceDir) {
    & (Join-Path $PSScriptRoot 'stop-metaos.ps1') -Instance $Instance -EnvFile $envPath

    New-Item -ItemType Directory -Force -Path $archiveRoot | Out-Null
    Move-Item -LiteralPath $instanceDir -Destination $archivedDir
    Write-Host "Archived instance '$Instance' to: $archivedDir"
}
else {
    Write-Host "Instance '$Instance' does not exist yet. Creating fresh instance."
}

if (-not $NoRestart) {
    & (Join-Path $PSScriptRoot 'start-metaos.ps1') -Instance $Instance -EnvFile $envPath
}
