@echo off
chcp 65001 > nul
echo ========================================
echo ChartChecker - 株式チャート生成ツール
echo ========================================
echo.

REM 現在のディレクトリを取得
set CURRENT_DIR=%~dp0
cd /d "%CURRENT_DIR%"

REM Pythonがインストールされているかチェック
python --version > nul 2>&1
if errorlevel 1 (
    echo エラー: Pythonがインストールされていません。
    echo Python 3.7以上をインストールしてください。
    pause
    exit /b 1
)

REM outputディレクトリの作成
if not exist "output" (
    mkdir output
    echo outputディレクトリを作成しました。
)

echo.
echo ChartCheckerを実行中...
echo.

REM ChartCheckerの実行
python chart_checker.py

if errorlevel 1 (
    echo.
    echo エラーが発生しました。ログファイル（chart_checker.log）を確認してください。
) else (
    echo.
    echo 処理が完了しました！
    echo 生成されたチャートはoutputディレクトリに保存されています。
)

echo.
echo 終了するには何かキーを押してください...
pause > nul