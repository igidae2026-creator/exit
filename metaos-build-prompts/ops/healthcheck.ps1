[CmdletBinding()]
param(
    [string]$Instance,
    [string]$EnvFile,
    [switch]$Json
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
$instanceDir = Join-Path (Join-Path $repoRoot $instancesDirName) $Instance
$pidFile = Join-Path $instanceDir 'metaos.pid'
$eventsFile = Join-Path $instanceDir 'events.jsonl'
$healthFile = Join-Path $instanceDir 'health.json'

$pid = $null
$running = $false
if (Test-Path -LiteralPath $pidFile) {
    $pid = Get-Content -LiteralPath $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($pid -and (Get-Process -Id $pid -ErrorAction SilentlyContinue)) {
        $running = $true
    }
}

$eventCount = 0
$lastEventAt = $null
if (Test-Path -LiteralPath $eventsFile) {
    $eventCount = (Get-Content -LiteralPath $eventsFile -ErrorAction SilentlyContinue | Measure-Object -Line).Lines
    $lastLine = Get-Content -LiteralPath $eventsFile -Tail 1 -ErrorAction SilentlyContinue
    if ($lastLine) {
        try {
            $obj = $lastLine | ConvertFrom-Json -ErrorAction Stop
            if ($obj.timestamp) {
                $lastEventAt = $obj.timestamp
            }
        }
        catch {
            $lastEventAt = $null
        }
    }
}

$result = [ordered]@{
    instance = $Instance
    running = $running
    pid = $pid
    events_file = $eventsFile
    events_count = $eventCount
    last_event_timestamp = $lastEventAt
    health_file = $healthFile
    checked_at = (Get-Date).ToString('o')
}

if ($Json) {
    $result | ConvertTo-Json
}
else {
    $result.GetEnumerator() | ForEach-Object {
        "{0}: {1}" -f $_.Key, $_.Value
    }
}

if ($running) { exit 0 } else { exit 1 }
