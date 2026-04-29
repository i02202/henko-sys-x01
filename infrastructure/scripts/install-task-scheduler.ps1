# Install the Henko-INTEL-DailyBriefing scheduled task on Windows.
#
# Replaces the WSL-internal cron job (which doesn't fire when WSL is
# hibernated). Windows Task Scheduler runs wsl.exe directly at 07:00 daily
# and uses StartWhenAvailable to catch up missed runs (PC was off, lid
# was closed, etc.) within 24h.
#
# History:
#   v1 (2026-04-27) used a PowerShell wrapper script for logging.
#       Failed under PS 5.1 (which is what Task Scheduler invokes by
#       default) due to a UTF-8-without-BOM em-dash in a comment line:
#       parser corrupted the file and exited with 0xFFFD0000 before
#       writing any log. Diagnosis was a rabbit hole because manual runs
#       under PS 7 worked fine.
#   v2 (2026-04-28) drops the wrapper entirely and has Task Scheduler
#       call wsl.exe directly. The briefing script handles its own
#       logging via stdout (captured to the briefing file's frontmatter)
#       and writes briefings to the WSL home dir. Success/failure is
#       observable via the briefing-file existence + dashboard.
#
# Run from PowerShell (any flavor; no admin needed):
#   powershell -ExecutionPolicy Bypass -NoProfile `
#     -File infrastructure\scripts\install-task-scheduler.ps1

$ErrorActionPreference = "Stop"

$BriefingScript = "/mnt/c/Users/Daniel Amer/henko-sys-x01/modules/intel/generate-briefing.py"
$TaskName       = "Henko-INTEL-DailyBriefing"

Write-Output "Henko Sys x01 Task Scheduler install"
Write-Output "  Briefing script: $BriefingScript"
Write-Output "  Task name:       $TaskName"
Write-Output ""

# Idempotent: drop any prior version of the task.
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Output "Removed prior task '$TaskName'"
}

# Action: directly invoke wsl.exe -- no PowerShell wrapper, no cmd shell.
# wsl.exe is in System32 (always on PATH), and the briefing script handles
# its own logging via stdout + the per-briefing YAML frontmatter.
$action = New-ScheduledTaskAction `
    -Execute "wsl.exe" `
    -Argument "-d Ubuntu -u daniel -- /usr/bin/python3 `"$BriefingScript`""

$trigger = New-ScheduledTaskTrigger -Daily -At "7:00am"

# Settings: catch missed runs, allow on battery, no idle wait, 20-min ceiling.
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopOnIdleEnd `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 20) `
    -MultipleInstances IgnoreNew

# Principal: run only when user is logged in, with the user's normal token.
# RunLevel Limited (no admin elevation) is fine: the briefing only writes
# to the user's WSL home dir.
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask `
    -TaskName    $TaskName `
    -Description "Henko Sys x01 daily INTEL Spanish AI briefing. Catches missed runs if PC was off at 07:00." `
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
Write-Output ""
Write-Output "WSL networking note: if you run a WireGuard VPN (ProtonVPN, etc.)"
Write-Output "with WSL2 mirrored networking enabled, the briefing's source"
Write-Output "fetches may fail with 'No route to host'. Either configure VPN"
Write-Output "split-tunnel to exclude WSL, or accept that the script will"
Write-Output "retry transient blips up to 3 times before giving up."
