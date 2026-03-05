[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet('start', 'stop', 'health', 'replay', 'rotate')]
    [string]$Command,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs
)

$ErrorActionPreference = 'Stop'

$scriptMap = @{
    start  = 'start-metaos.ps1'
    stop   = 'stop-metaos.ps1'
    health = 'healthcheck.ps1'
    replay = 'replay.ps1'
    rotate = 'rotate-instance.ps1'
}

$target = Join-Path $PSScriptRoot $scriptMap[$Command]
if (-not (Test-Path -LiteralPath $target)) {
    throw "Command script not found: $target"
}

& $target @RemainingArgs
exit $LASTEXITCODE
