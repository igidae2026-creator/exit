[CmdletBinding()]
param(
    [string]$Instance,
    [string]$EnvFile,
    [int]$Limit,
    [switch]$Raw,
    [switch]$AsJson
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
if (-not $Limit -or $Limit -le 0) {
    $Limit = if ($env:METAOS_REPLAY_LIMIT) { [int]$env:METAOS_REPLAY_LIMIT } else { 100 }
}

$rootRel = if ($env:METAOS_ROOT) { $env:METAOS_ROOT } else { '..' }
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot $rootRel)
$instancesDirName = if ($env:METAOS_INSTANCES_DIR) { $env:METAOS_INSTANCES_DIR } else { 'instances' }
$eventsFile = Join-Path (Join-Path (Join-Path $repoRoot $instancesDirName) $Instance) 'events.jsonl'

if (-not (Test-Path -LiteralPath $eventsFile)) {
    throw "events.jsonl not found for instance '$Instance': $eventsFile"
}

$lines = Get-Content -LiteralPath $eventsFile -Tail $Limit
if ($Raw) {
    $lines | ForEach-Object { $_ }
    exit 0
}

$items = @()
foreach ($line in $lines) {
    if (-not $line) { continue }
    try {
        $obj = $line | ConvertFrom-Json -ErrorAction Stop
        $items += $obj
    }
    catch {
        $items += [pscustomobject]@{
            timestamp = $null
            event_type = 'parse_error'
            payload = $line
        }
    }
}

if ($AsJson) {
    $items | ConvertTo-Json -Depth 20
}
else {
    foreach ($item in $items) {
        $ts = if ($item.timestamp) { $item.timestamp } else { '-' }
        $ty = if ($item.event_type) { $item.event_type } else { '-' }
        Write-Host ("{0} | {1}" -f $ts, $ty)
    }
}
