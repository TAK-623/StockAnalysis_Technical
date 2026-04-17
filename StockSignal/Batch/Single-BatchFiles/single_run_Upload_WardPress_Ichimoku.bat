@echo off
cd /d %~dp0..\..
chcp 65001 > nul
echo Upload_WardPress_Ichimoku.py を実行します...
python Upload_WardPress_Ichimoku.py
pause
