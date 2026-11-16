$ErrorActionPreference = 'Stop'

function Find-RuntimePayloadSource {
    param(
        [Parameter(Mandatory = $true)][string]$SkillName,
        [Parameter(Mandatory = $true)][string]$ArchiveName,
        [Parameter(Mandatory = $true)][string]$BootstrapRoot,
        [string]$DefaultUrl = ''
    )

    $skillEnvName = (($SkillName -replace '-', '_').ToUpperInvariant() + '_FILE_SERVER')
    $override = [Environment]::GetEnvironmentVariable($skillEnvName)
    if (-not $override) { $override = $env:LOCAL_SKILL_FILE_SERVER }
    if ($override -and $override -match '^https?://') {
        return "$($override.TrimEnd('/'))/$ArchiveName"
    }
    if ($override) {
        if (Test-Path -LiteralPath $override -PathType Leaf) {
            return (Resolve-Path -LiteralPath $override).Path
        }
        $overrideArchive = Join-Path $override $ArchiveName
        if (Test-Path -LiteralPath $overrideArchive -PathType Leaf) {
            return (Resolve-Path -LiteralPath $overrideArchive).Path
        }
    }

    # Local development fallback: walk upward to the repository file-server.
    $cursor = Get-Item -LiteralPath $BootstrapRoot
    while ($cursor) {
        $candidate = Join-Path $cursor.FullName "file-server\$ArchiveName"
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
        $cursor = $cursor.Parent
    }

    if ($DefaultUrl -match '^https?://') { return $DefaultUrl }
    throw "Runtime payload '$ArchiveName' was not found and no download URL is configured. Set $skillEnvName or LOCAL_SKILL_FILE_SERVER to a file-server directory or HTTP(S) base URL."
}

function Install-SkillRuntimePayload {
    param(
        [Parameter(Mandatory = $true)][string]$SkillName,
        [Parameter(Mandatory = $true)][string]$ManifestPath
    )

    $manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
    foreach ($field in @('archive')) {
        if (-not $manifest.$field) { throw "Runtime payload manifest is missing '$field'." }
    }

    $bootstrapRoot = Split-Path -Parent $ManifestPath
    $runtimeBase = Join-Path $env:USERPROFILE ".openvino\runtime\$SkillName"
    $runtimeRoot = Join-Path $runtimeBase 'current'
    $readyMarker = Join-Path $runtimeRoot '.runtime-ready'
    if ((Test-Path -LiteralPath $readyMarker) -and
        (Test-Path -LiteralPath (Join-Path $runtimeRoot 'scripts\run.ps1'))) {
        return $runtimeRoot
    }

    $downloadDir = Join-Path $env:USERPROFILE '.openvino\downloads'
    New-Item -ItemType Directory -Path $downloadDir -Force | Out-Null
    $cachedArchive = Join-Path $downloadDir ([string]$manifest.archive)
    $source = Find-RuntimePayloadSource `
        -SkillName $SkillName `
        -ArchiveName ([string]$manifest.archive) `
        -BootstrapRoot $bootstrapRoot `
        -DefaultUrl ([string]$manifest.url)
    $partialArchive = "$cachedArchive.partial-$PID"
    Remove-Item -LiteralPath $partialArchive -Force -ErrorAction SilentlyContinue
    Write-Host "首次运行，正在下载 $SkillName 运行组件..."
    try {
        if ($source -match '^https?://') {
            $null = Invoke-WebRequest -UseBasicParsing -Uri $source -OutFile $partialArchive -TimeoutSec 300
        } else {
            Copy-Item -LiteralPath $source -Destination $partialArchive -Force
        }
        Remove-Item -LiteralPath $cachedArchive -Force -ErrorAction SilentlyContinue
        Move-Item -LiteralPath $partialArchive -Destination $cachedArchive
    }
    catch {
        Remove-Item -LiteralPath $partialArchive -Force -ErrorAction SilentlyContinue
        if (-not (Test-Path -LiteralPath $cachedArchive)) { throw }
        Write-Warning "Runtime download failed; using the existing cached archive for $SkillName."
    }

    New-Item -ItemType Directory -Path $runtimeBase -Force | Out-Null
    $stagingRoot = "$runtimeRoot.partial-$PID-$([guid]::NewGuid().ToString('N'))"
    try {
        Expand-Archive -LiteralPath $cachedArchive -DestinationPath $stagingRoot -Force
        $runtimeEntry = Join-Path $stagingRoot 'scripts\run.ps1'
        if (-not (Test-Path -LiteralPath $runtimeEntry)) {
            throw 'Runtime payload is incomplete: missing scripts\run.ps1.'
        }
        Set-Content -LiteralPath (Join-Path $stagingRoot '.runtime-ready') -Value 'ready' -Encoding ASCII
        if (Test-Path -LiteralPath $runtimeRoot) {
            Remove-Item -LiteralPath $runtimeRoot -Recurse -Force
        }
        Move-Item -LiteralPath $stagingRoot -Destination $runtimeRoot
    }
    finally {
        if (Test-Path -LiteralPath $stagingRoot) {
            Remove-Item -LiteralPath $stagingRoot -Recurse -Force
        }
    }
    return $runtimeRoot
}
