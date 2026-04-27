# Henko Sys x01 — INTEL daily briefing wrapper for Windows Task Scheduler.
#
# Why this exists: WSL2's internal cron only fires when WSL is running.
# WSL2 enters idle ~8s after the last process exits, and there is no
# wake-on-cron — if Windows is asleep or WSL is hibernated at 07:00, the
# briefing simply skips that day with no retry.
#
# This wrapper runs from Windows Task Scheduler. Task Scheduler honors
# `runIfMissed` semantics, so a briefing that would have been skipped
# (PC was off, lid was closed) fires when the machine wakes. The wrapper
# starts WSL on demand — no need for WSL to be already running.
#
# Logs land in %LOCALAPPDATA%\HenkoSysX01\logs\ alongside this script.

$ErrorActionPreference = "Stop"
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$logDir = Join-Path $PSScriptRoot "logs"
$logFile = Join-Path $logDir "briefing-$timestamp.log"
New-Item -Path $logDir -ItemType Directory -Force | Out-Null

function Write-Log {
    param([string]$Message)
    $line = "[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $Message
    Add-Content -Path $logFile -Value $line -Encoding utf8
    Write-Output $line
}

Write-Log "=== Henko INTEL briefing wrapper start ==="
Write-Log "Log file: $logFile"

# Verify WSL is reachable. wsl.exe will boot the distro if needed.
Write-Log "Checking WSL Ubuntu availability..."
$wslOut = & wsl -d Ubuntu -- echo "wsl_ok" 2>&1
if ($LASTEXITCODE -ne 0 -or $wslOut -notmatch "wsl_ok") {
    Write-Log "ERROR: WSL Ubuntu unreachable. Output: $wslOut"
    exit 2
}
Write-Log "WSL Ubuntu OK."

# Run the briefing generator as user `daniel` (the user who owns Paperclip
# data + cron + briefings dir). Pass MSYS_NO_PATHCONV so the /mnt path
# isn't mangled if the parent process is bash-flavored.
Write-Log "Invoking generate-briefing.py..."
$env:MSYS_NO_PATHCONV = "1"
$briefingOut = & wsl -d Ubuntu -u daniel -- /usr/bin/python3 "/mnt/c/Users/Daniel Amer/henko-sys-x01/modules/intel/generate-briefing.py" 2>&1
$briefingExit = $LASTEXITCODE
$briefingOut | ForEach-Object { Write-Log "  | $_" }

if ($briefingExit -eq 0) {
    Write-Log "=== SUCCESS (exit 0) ==="
    exit 0
} else {
    Write-Log "=== FAILED (exit $briefingExit) ==="
    exit $briefingExit
}
