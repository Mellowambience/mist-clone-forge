@echo off
title MIST mesh + phone
cd /d "%~dp0"
echo.
echo  Stopping old 8766 listeners...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8766" ^| findstr "LISTENING"') do taskkill /F /PID %%p >nul 2>&1
timeout /t 2 /nobreak >nul

echo  Starting mesh on ALL interfaces (0.0.0.0:8766)...
set MIST_HOST=0.0.0.0
set MIST_PORT=8766
REM Hidden durable process with log files (survives this window closing)
powershell -NoProfile -Command ^
  "Start-Process -FilePath 'C:\Python310\python.exe' -ArgumentList '-u','mist_serve.py' -WorkingDirectory '%~dp0' -WindowStyle Hidden -RedirectStandardOutput '%~dp0serve_stdout.log' -RedirectStandardError '%~dp0serve_stderr.log'"

timeout /t 5 /nobreak >nul
echo.
powershell -NoProfile -Command ^
  "try { $a=Invoke-RestMethod http://127.0.0.1:8766/api/carrier -TimeoutSec 3; Write-Host ('OK  MESH ' + $a.status + ' agents=' + $a.agents) } catch { Write-Host 'FAIL local — see mist_serve.log / serve_stderr.log'; exit 1 }; " ^
  "try { Invoke-RestMethod http://10.0.0.107:8766/api/carrier -TimeoutSec 3 | Out-Null; Write-Host 'OK  LAN  http://10.0.0.107:8766/tv' } catch { Write-Host 'WARN LAN IP check failed' }; " ^
  "Write-Host ''; Write-Host 'PHONE (same Wi-Fi as PC):'; Write-Host '  http://10.0.0.107:8766/tv'; Write-Host ''; Write-Host 'If phone says refused: double-click ALLOW_PHONE_FIREWALL.bat (Admin once)'"

start "" "http://127.0.0.1:8766/"
start "" "http://127.0.0.1:8766/tv"
echo.
echo  Server is running hidden. This window can close.
echo  Re-run this bat if the page dies again.
pause
