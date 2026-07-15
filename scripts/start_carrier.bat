@echo off
title MIST Carrier — keep :8766 LOCKED
cd /d "%~dp0"
echo.
echo  MIST CARRIER
echo  Holds Agentic Vision + Swarm Ops on http://127.0.0.1:8766/
echo  Leave this window open.
echo.
REM free dead listeners
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8766" ^| findstr "LISTENING"') do taskkill /F /PID %%p >nul 2>&1
timeout /t 1 /nobreak >nul

:loop
echo [%date% %time%] starting swarm_board.py ...
start "MIST-Mesh-8766" /MIN python -u swarm_board.py --port 8766 --host 127.0.0.1
timeout /t 4 /nobreak >nul

:check
powershell -NoProfile -Command "try { $r=Invoke-RestMethod http://127.0.0.1:8766/api/carrier -TimeoutSec 2; if($r.locked){ Write-Host ('CARRIER LOCK · up=' + $r.uptime_human + ' · agents=' + $r.agents + ' · ' + $r.signal_label); exit 0 } else { exit 1 } } catch { Write-Host 'NO CARRIER'; exit 1 }"
if errorlevel 1 (
  echo [%date% %time%] lost carrier — restarting in 3s
  for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8766" ^| findstr "LISTENING"') do taskkill /F /PID %%p >nul 2>&1
  timeout /t 3 /nobreak >nul
  goto loop
)
timeout /t 8 /nobreak >nul
goto check
