# MIST Carrier Watch — keeps Agentic Vision / Swarm Ops on :8766
# Run: powershell -ExecutionPolicy Bypass -File carrier_watch.ps1

$ErrorActionPreference = "SilentlyContinue"
$Port = 8766
$Wd = Split-Path -Parent $MyInvocation.MyCommand.Path
$Url = "http://127.0.0.1:$Port/api/carrier"
$Py = "python.exe"

Write-Host "MIST Carrier Watch · port $Port · Ctrl+C to stop"
Write-Host "Working dir: $Wd"

function Test-Carrier {
  try {
    $r = Invoke-RestMethod -Uri $Url -TimeoutSec 2
    return $r.locked -eq $true -or $r.status -eq "LOCKED"
  } catch {
    return $false
  }
}

function Start-Board {
  Write-Host "$(Get-Date -Format o) · NO CARRIER — starting swarm_board.py"
  Start-Process -FilePath $Py -ArgumentList "swarm_board.py","--port","$Port","--host","127.0.0.1" `
    -WorkingDirectory $Wd -WindowStyle Minimized
  Start-Sleep -Seconds 3
}

if (-not (Test-Carrier)) { Start-Board }

while ($true) {
  if (Test-Carrier) {
    try {
      $s = Invoke-RestMethod -Uri $Url -TimeoutSec 2
      Write-Host "$(Get-Date -Format HH:mm:ss) · CARRIER LOCK · bars=$($s.signal_label) · up=$($s.uptime_human) · agents=$($s.agents)"
    } catch {}
  } else {
    # free stuck listeners
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
      ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Seconds 1
    Start-Board
  }
  Start-Sleep -Seconds 8
}
