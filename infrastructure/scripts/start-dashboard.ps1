# Henko Mission Control — launcher.
#
# Picks the first non-Microsoft-Store Python on the system to run the
# dashboard server. Microsoft Store Python sandboxes %LOCALAPPDATA%, which
# breaks the Ollama log + wrapper log probes. The python.org install at
# AppData\Local\Programs\Python\... has no such restriction.
#
# Run from PowerShell (any profile, no admin needed):
#   powershell -ExecutionPolicy Bypass -NoProfile `
#     -File infrastructure\scripts\start-dashboard.ps1

$ErrorActionPreference = "Stop"

$RepoRoot   = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$ServerPath = Join-Path $RepoRoot "modules\dashboard\server.py"

if (-not (Test-Path $ServerPath)) {
    throw "server.py not found at $ServerPath"
}

# Candidate Python paths in priority order. First one that exists wins.
$candidates = @(
    "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "$env:ProgramFiles\Python313\python.exe",
    "$env:ProgramFiles\Python312\python.exe"
)

$python = $null
foreach ($p in $candidates) {
    if (Test-Path $p) { $python = $p; break }
}

if (-not $python) {
    Write-Warning "No non-Store Python found at:"
    $candidates | ForEach-Object { Write-Warning "  $_" }
    Write-Warning "Falling back to whatever 'python' resolves to in PATH."
    Write-Warning "(If that is the Store version, log probes will fail - see server.py docstring.)"
    $python = "python"
}

Write-Output "Henko Mission Control"
Write-Output "  Python:  $python"
Write-Output "  Server:  $ServerPath"
Write-Output ""

& $python $ServerPath
