$principal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell.exe -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit
}
while ($true) {
    Write-Host "`nAI课件协作 · 局域网原型管理" -ForegroundColor Cyan
    Write-Host '1 打开预览首页   2 查看状态   3 发布当前原型   4 回滚上次发布'
    Write-Host '5 启动服务       6 停止服务   0 退出'
    $choice=Read-Host '请输入数字'
    if($choice -eq '0'){break}
    if($choice -eq '1'){Start-Process 'http://127.0.0.1:8769/';continue}
    $actions=@{'2'='状态';'3'='更新';'4'='回滚';'5'='启动';'6'='停止'}
    if($actions.ContainsKey($choice)){try{& "$PSScriptRoot\管理服务.ps1" $actions[$choice]}catch{Write-Host $_ -ForegroundColor Red}}
}
