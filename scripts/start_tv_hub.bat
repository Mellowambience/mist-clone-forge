@echo off
title MIST Agentic Vision :8766
cd /d "%~dp0"
echo.
echo  MIST Agentic Vision  -  live cognition surface
echo  http://127.0.0.1:8766/tv
echo  Leave this window OPEN.
echo.
start "" "http://127.0.0.1:8766/tv"
python swarm_board.py --port 8766 --host 127.0.0.1
if errorlevel 1 (
  echo.
  echo Failed. Is Python installed?
  pause
)
