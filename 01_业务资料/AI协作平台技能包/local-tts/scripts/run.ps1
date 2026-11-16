$ErrorActionPreference = 'Stop'

# This script intentionally has no param block. PowerShell collects every
# caller argument in $args, which lets one bootstrap entry point transparently
# forward the different argument contracts used by all local skills.
$ForwardArgs = @($args)
$BootstrapRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

# Keep the AIPC gate in the lightweight package so unsupported machines fail
# before downloading the larger runtime payload.
$PlatformExe = Join-Path $BootstrapRoot 'bin\platform.exe'
if (Test-Path -LiteralPath $PlatformExe) {
    $isAipc = [string](& $PlatformExe --is-aipc)
    if ([string]::IsNullOrWhiteSpace($isAipc)) {
        # platform.exe may not emit capturable output under non-interactive redirection; skip the check
        Write-Host 'WARN: platform.exe produced no output; skipping AIPC check.'
    } elseif ($isAipc.Trim() -ne '1') {
        Write-Host 'This skill requires an Intel AIPC platform.'
        exit 1
    }
} else {
    Write-Host 'WARN: bin\platform.exe missing; skipping AIPC check.'
}

$ManifestPath = Join-Path $BootstrapRoot 'runtime-payload.json'
$PayloadHelper = Join-Path $PSScriptRoot 'runtime-payload.ps1'
if (-not (Test-Path -LiteralPath $ManifestPath)) {
    Write-Host 'ERROR: runtime-payload.json not found.'
    exit 1
}
if (-not (Test-Path -LiteralPath $PayloadHelper)) {
    Write-Host 'ERROR: scripts\runtime-payload.ps1 not found.'
    exit 1
}

. $PayloadHelper
try {
    $manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
    $RuntimeRoot = Install-SkillRuntimePayload `
        -SkillName ([string]$manifest.skill_name) `
        -ManifestPath $ManifestPath
}
catch {
    Write-Host "ERROR: $($_.Exception.Message)"
    exit 1
}

$RuntimeEntry = Join-Path $RuntimeRoot 'scripts\run.ps1'
& $RuntimeEntry @ForwardArgs
exit $LASTEXITCODE
