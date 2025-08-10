@echo off
chcp 65001 > nul
echo ===================================
echo WordPress to X Posting Script
echo ===================================
echo.

:: Python実行パスの設定
set PYTHON_PATH=python

:: スクリプトのパスを固定
set SCRIPT_PATH=C:\Users\mount\Git\StockAnalysis_Technical\X_twitter\post_wp_to_x.py

echo スクリプトのパス: %SCRIPT_PATH%
echo スクリプトを実行します...

:: スクリプトの存在確認
if not exist "%SCRIPT_PATH%" (
    echo エラー: スクリプトが見つかりません: %SCRIPT_PATH%
    goto :error
)

%PYTHON_PATH% "%SCRIPT_PATH%"

if %ERRORLEVEL% NEQ 0 (
    goto :error
)

echo.
echo 実行完了しました。
goto :end

:error
echo.
echo エラーが発生しました。
echo - Pythonがインストールされていることを確認してください。
echo - スクリプトパスが正しいことを確認してください。
echo   現在のパス: %SCRIPT_PATH%

:end
echo.
echo 10秒後に自動的に終了します...
timeout /t 10
exit