[CmdletBinding()]
param(
    [string]$Instance,
    [string]$EnvFile,
    [int]$TimeoutSec
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

if (-not $TimeoutSec -or $TimeoutSec -le 0) {
    $TimeoutSec = if ($env:METAOS_STOP_TIMEOUT_SEC) { [int]$env:METAOS_STOP_TIMEOUT_SEC } else { 20 }
}

$rootRel = if ($env:METAOS_ROOT) { $env:METAOS_ROOT } else { '..' }
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot $rootRel)
$instancesDirName = if ($env:METAOS_INSTANCES_DIR) { $env:METAOS_INSTANCES_DIR } else { 'instances' }
$instanceDir = Join-Path (Join-Path $repoRoot $instancesDirName) $Instance
$pidFile = Join-Path $instanceDir 'metaos.pid'
$healthFile = Join-Path $instanceDir 'health.json'

if (-not (Test-Path -LiteralPath $pidFile)) {
    Write-Host "No running PID file for instance '$Instance'."
    exit 0
}

$pid = Get-Content -LiteralPath $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $pid) {
    Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
    Write-Host "Stale PID file removed for instance '$Instance'."
    exit 0
}

$process = Get-Process -Id $pid -ErrorAction SilentlyContinue
if (-not $process) {
    Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
    Write-Host "Process $pid not running. Cleaned stale PID file."
    exit 0
}

Write-Host "Stopping METAOS instance '$Instance' (PID $pid)..."
Stop-Process -Id $pid -ErrorAction SilentlyContinue

$deadline = (Get-Date).AddSeconds($TimeoutSec)
while ((Get-Date) -lt $deadline) {
    if (-not (Get-Process -Id $pid -ErrorAction SilentlyContinue)) {
        break
    }
    Start-Sleep -Milliseconds 300
}

if (Get-Process -Id $pid -ErrorAction SilentlyContinue) {
    Stop-Process -Id $pid -Force
}

Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue

$status = [ordered]@{
    instance = $Instance
    pid = $pid
    status = 'stopped'
    stopped_at = (Get-Date).ToString('o')
}
$status | ConvertTo-Json | Set-Content -LiteralPath $healthFile

Write-Host "Stopped METAOS instance '$Instance'."
