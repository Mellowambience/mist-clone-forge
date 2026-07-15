@echo off
:: Requests Administrator to allow phone Wi-Fi into MIST on port 8766
net session >nul 2>&1
if %errorlevel% NEQ 0 (
  echo Requesting Administrator for firewall rule...
  powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)
echo Adding firewall rule: MIST Mesh 8766 (private profile)...
netsh advfirewall firewall delete rule name="MIST Mesh 8766" >nul 2>&1
netsh advfirewall firewall add rule name="MIST Mesh 8766" dir=in action=allow protocol=TCP localport=8766 profile=private
netsh advfirewall firewall add rule name="MIST Mesh 8766 Public" dir=in action=allow protocol=TCP localport=8766 profile=public
echo.
echo Done. On your phone (same Wi-Fi) open:
echo   http://10.0.0.107:8766/tv
echo.
pause
