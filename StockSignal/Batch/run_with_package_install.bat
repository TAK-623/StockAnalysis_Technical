@echo off
cd /d %~dp0..
chcp 65001 > nul
echo 依存パッケージをインストールして株価シグナル処理を実行します...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo パッケージのインストールに失敗しました。
    pause
    exit /b 1
)
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo エラーが発生しました。
    pause
    exit /b 1
)
echo 処理が正常に完了しました。
pause
