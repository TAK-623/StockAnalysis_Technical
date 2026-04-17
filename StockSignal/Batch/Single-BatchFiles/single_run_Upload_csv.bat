@echo off
cd /d %~dp0..\..
chcp 65001 > nul
echo Upload_csv.py を実行します...
python Upload_csv.py
pause
