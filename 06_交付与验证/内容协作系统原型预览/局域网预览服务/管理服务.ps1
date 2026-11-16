param([ValidateSet('安装','启动','停止','状态','更新','回滚','卸载')][string]$Action='状态')
$ErrorActionPreference='Stop'
$taskName='AI-Course-Prototype-LAN'
$firewallName='AI-Course-Prototype-LAN-8769'
switch($Action){
 '安装' {
   $exe="$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
   $taskAction=New-ScheduledTaskAction -Execute $exe -Argument "-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$PSScriptRoot\后台运行.ps1`"" -WorkingDirectory $PSScriptRoot
   $trigger=New-ScheduledTaskTrigger -AtStartup
   $principal=New-ScheduledTaskPrincipal -UserId 'NT AUTHORITY\LOCAL SERVICE' -LogonType ServiceAccount -RunLevel Limited
   $settings=New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
   & icacls.exe $PSScriptRoot /grant '*S-1-5-19:(OI)(CI)RX' /T /Q | Out-Null
   & icacls.exe "$PSScriptRoot\logs" /grant '*S-1-5-19:(OI)(CI)M' /T /Q | Out-Null
   if(-not (Get-NetFirewallRule -Name $firewallName -ErrorAction SilentlyContinue)){New-NetFirewallRule -Name $firewallName -DisplayName 'AI课件原型局域网预览' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8769 -RemoteAddress LocalSubnet -Profile Domain,Private -Program "$PSScriptRoot\runtime\node.exe" | Out-Null}
   Register-ScheduledTask -TaskName $taskName -Action $taskAction -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
   Start-ScheduledTask -TaskName $taskName
 }
 '启动' {Enable-ScheduledTask -TaskName $taskName | Out-Null;Start-ScheduledTask -TaskName $taskName}
 '停止' {Disable-ScheduledTask -TaskName $taskName | Out-Null;Stop-ScheduledTask -TaskName $taskName}
 '状态' {Get-ScheduledTask -TaskName $taskName | Format-List TaskName,State;Get-ScheduledTaskInfo -TaskName $taskName | Format-List LastRunTime,LastTaskResult;try{Invoke-RestMethod 'http://127.0.0.1:8769/healthz' | Format-List}catch{Write-Output '服务当前不可访问'}}
 '更新' {& "$PSScriptRoot\runtime\node.exe" "$PSScriptRoot\publish.cjs" activate;if($LASTEXITCODE -ne 0){throw '发布失败，旧版本保持不变'}}
 '回滚' {& "$PSScriptRoot\runtime\node.exe" "$PSScriptRoot\publish.cjs" rollback;if($LASTEXITCODE -ne 0){throw '回滚失败'}}
 '卸载' {Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue;Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue;Remove-NetFirewallRule -Name $firewallName -ErrorAction SilentlyContinue}
}
