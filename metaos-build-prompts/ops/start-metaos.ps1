[CmdletBinding()]
param(
    [string]$Instance,
    [string]$EnvFile,
    [switch]$InstallRuntime
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
$logsDir = Join-Path $instanceDir 'logs'
$eventsFile = Join-Path $instanceDir 'events.jsonl'
$pidFile = Join-Path $instanceDir 'metaos.pid'
$outLog = Join-Path $logsDir 'stdout.log'
$errLog = Join-Path $logsDir 'stderr.log'

New-Item -ItemType Directory -Force -Path $instancesRoot, $instanceDir, $logsDir | Out-Null
if (-not (Test-Path -LiteralPath $eventsFile)) {
    New-Item -ItemType File -Path $eventsFile | Out-Null
}

if (Test-Path -LiteralPath $pidFile) {
    $existingPid = Get-Content -LiteralPath $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($existingPid -and (Get-Process -Id $existingPid -ErrorAction SilentlyContinue)) {
        Write-Host "METAOS instance '$Instance' already running (PID $existingPid)."
        exit 0
    }
    Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
}

if ($InstallRuntime) {
    & (Join-Path $PSScriptRoot 'install-runtime.ps1') -EnvFile $envPath
}

$python = if ($env:METAOS_PYTHON) { $env:METAOS_PYTHON } else { 'python' }
if (-not (Get-Command $python -ErrorAction SilentlyContinue)) {
    throw "Python runtime command not found: $python"
}

$entrypointRel = if ($env:METAOS_ENTRYPOINT) { $env:METAOS_ENTRYPOINT } else { 'runtime/orchestrator.py' }
$entrypoint = Join-Path $repoRoot $entrypointRel
if (-not (Test-Path -LiteralPath $entrypoint)) {
    throw "Runtime entrypoint not found: $entrypoint"
}

# Expose instance context to runtime.
$env:METAOS_INSTANCE = $Instance
$env:METAOS_INSTANCE_DIR = $instanceDir
$env:METAOS_EVENTS_FILE = $eventsFile

$argList = @($entrypoint)
if ($env:METAOS_RUNTIME_ARGS) {
    $extra = [System.Management.Automation.PSParser]::Tokenize($env:METAOS_RUNTIME_ARGS, [ref]$null) |
        Where-Object { $_.Type -in 'CommandArgument', 'String' } |
        ForEach-Object { $_.Content }
    if ($extra) {
        $argList += $extra
    }
}

$proc = Start-Process -FilePath $python -ArgumentList $argList -WorkingDirectory $repoRoot -NoNewWindow -RedirectStandardOutput $outLog -RedirectStandardError $errLog -PassThru
Set-Content -LiteralPath $pidFile -Value $proc.Id

$status = [ordered]@{
    instance = $Instance
    pid = $proc.Id
    status = 'running'
    started_at = (Get-Date).ToString('o')
    entrypoint = $entrypointRel
    events_file = $eventsFile
}
$status | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $instanceDir 'health.json')

Write-Host "Started METAOS instance '$Instance' (PID $($proc.Id))."
Write-Host "Logs: $logsDir"
Write-Host "Events: $eventsFile"
