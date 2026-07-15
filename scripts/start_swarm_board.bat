@echo off
title MIST Swarm Ops :8766
cd /d "%~dp0"
echo.
echo  MIST Swarm Ops  —  specialists, not tickets
echo  http://127.0.0.1:8766/
echo  Leave this window OPEN or the board dies.
echo.
start "" "http://127.0.0.1:8766/"
python swarm_board.py --port 8766 --host 127.0.0.1
if errorlevel 1 (
  echo.
  echo Board failed to start. Is Python installed?
  pause
)
