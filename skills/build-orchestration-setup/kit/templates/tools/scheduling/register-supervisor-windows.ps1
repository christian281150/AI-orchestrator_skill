# Registers the supervisor as a Windows scheduled task that starts at logon and restarts on failure.
# Run once in PowerShell from the repository root:  powershell -ExecutionPolicy Bypass -File tools\scheduling\register-supervisor-windows.ps1
# ASCII only on purpose: Windows PowerShell 5.1 misreads UTF-8 files without a BOM.
$ErrorActionPreference = 'Stop'
$repo   = (Resolve-Path "$PSScriptRoot\..\..").Path
$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) { $python = (Get-Command py).Source }
$name   = '{{PROJECT_NAME}}-supervisor'
$action = New-ScheduledTaskAction -Execute $python -Argument "`"$repo\tools\orch.py`" --config `"$repo\orchestration.toml`" supervise" -WorkingDirectory $repo
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
  -RestartCount 99 -RestartInterval (New-TimeSpan -Minutes 5) -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
Write-Output "Registered '$name'. Start now:  Start-ScheduledTask -TaskName '$name'"
Write-Output "Stop cleanly: create docs\coordination\STOP (the supervisor exits between rounds). Never kill a running round."
Write-Output "Also set: Power & sleep -> never sleep while plugged in, or rounds pause with the PC."
