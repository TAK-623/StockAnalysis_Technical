@echo off
cd /d %~dp0..
chcp 65001 > nul
echo ROE情報の追加処理を開始します...
python add_roe_to_breakout.py
pause
