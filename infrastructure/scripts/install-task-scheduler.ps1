# Install the Henko-INTEL-DailyBriefing scheduled task on Windows.
#
# Replaces the WSL-internal cron job (which doesn't fire when WSL is
# hibernated). Windows Task Scheduler runs the wrapper at 07:00 daily
# and uses StartWhenAvailable to catch up missed runs (PC was off, lid
# was closed, etc.) within 24h.
#
# Run from PowerShell:
#   powershell -ExecutionPolicy Bypass -NoProfile -File infrastructure\scripts\install-task-scheduler.ps1

$ErrorActionPreference = "Stop"

$RepoRoot      = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$RepoWrapper   = Join-Path $PSScriptRoot "run-intel-briefing.ps1"
$DeployDir     = Join-Path $env:LOCALAPPDATA "HenkoSysX01"
$DeployWrapper = Join-Path $DeployDir "run-intel-briefing.ps1"
$DeployLogDir  = Join-Path $DeployDir "logs"
$TaskName      = "Henko-INTEL-DailyBriefing"

Write-Output "Henko Sys x01 — Task Scheduler install"
Write-Output "  Repo wrapper:   $RepoWrapper"
Write-Output "  Deploy target:  $DeployWrapper"
Write-Output "  Task name:      $TaskName"
Write-Output ""

if (-not (Test-Path $RepoWrapper)) {
    throw "Wrapper not found at $RepoWrapper — run from a checked-out repo."
}

# Stage the wrapper into LOCALAPPDATA (Task Scheduler points at this stable path).
New-Item -Path $DeployDir    -ItemType Directory -Force | Out-Null
New-Item -Path $DeployLogDir -ItemType Directory -Force | Out-Null
Copy-Item -Path $RepoWrapper -Destination $DeployWrapper -Force
Write-Output "Staged wrapper to $DeployWrapper"

# Idempotent: drop any prior version of the task.
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Output "Removed prior task '$TaskName'"
}

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File `"$DeployWrapper`""

$trigger = New-ScheduledTaskTrigger -Daily -At "7:00am"

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopOnIdleEnd `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 20) `
    -MultipleInstances IgnoreNew

$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask `
    -TaskName    $TaskName `
    -Description "Henko Sys x01 — daily INTEL Spanish AI briefing. Catches missed runs if PC was off at 07:00." `
    -Action      $action `
    -Trigger     $trigger `
    -Settings    $settings `
    -Principal   $principal | Out-Null

Write-Output ""
Write-Output "Installed. Next run:"
Get-ScheduledTask -TaskName $TaskName |
    Select-Object TaskName, State,
        @{N="NextRun";E={(Get-ScheduledTaskInfo -TaskName $_.TaskName).NextRunTime}} |
    Format-List

Write-Output "Don't forget: disable the WSL-internal cron job to avoid duplicate runs."
Write-Output "  wsl -d Ubuntu -u daniel -- bash -c 'crontab -l | grep -v generate-briefing.py | crontab -'"
