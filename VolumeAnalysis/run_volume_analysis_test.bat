@echo off
cd /d %~dp0
chcp 65001 > nul
echo 出来高移動平均算出ツール（テストモード）を実行します...
python main.py --test
echo 処理が完了しました。
pause