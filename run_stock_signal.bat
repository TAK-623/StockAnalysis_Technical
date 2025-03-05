@echo off
cd /d %~dp0
chcp 65001 > nul
echo 株価データ取得ツール（通常モード）を実行します...
python main.py
echo 処理が完了しました。
pause