# Start MIST Swarm Board and keep it alive (own window).
# Usage: right-click Run with PowerShell, or:
#   powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.grok\mist-clones\scripts\start_swarm_board.ps1"

$ErrorActionPreference = "SilentlyContinue"
$Port = 8766
$Script = Join-Path $PSScriptRoot "swarm_board.py"
$Url = "http://127.0.0.1:$Port/"

# free port if a dead/half-open owner
Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Start-Sleep -Milliseconds 400

# already healthy?
try {
  $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 1
  if ($r.StatusCode -eq 200) {
    Write-Host "Board already running → $Url"
    Start-Process $Url
    exit 0
  }
} catch {}

if (-not (Test-Path $Script)) {
  Write-Host "Missing $Script"
  exit 1
}

Write-Host "Starting MIST Swarm Board on $Url"
Write-Host "Leave this window open while you watch the board."
Write-Host "Ctrl+C stops the board."
Write-Host ""

# open browser after short delay in background job
Start-Job -ScriptBlock {
  param($u)
  Start-Sleep -Seconds 1
  Start-Process $u
} -ArgumentList $Url | Out-Null

# run in THIS console so it stays up (not killed with parent agent shells)
python $Script --port $Port --host 127.0.0.1
