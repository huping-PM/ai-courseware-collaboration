$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
while ($true) {
    & "$PSScriptRoot\runtime\node.exe" "$PSScriptRoot\server.cjs"
    Add-Content -LiteralPath "$PSScriptRoot\logs\supervisor.log" -Value "$(Get-Date -Format o) Server exited; restart in 5 seconds."
    Start-Sleep -Seconds 5
}
