@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo ====================================
echo 株式評価損益計算ツール実行バッチ
echo ====================================
echo.

echo 2週間前の日付を自動計算中...

:: PowerShellで1週間前の日付を計算
for /f %%i in ('powershell -NoProfile -Command "(Get-Date).AddDays(-14).ToString('yyyyMMdd')"') do set SIGNAL_DATE=%%i

:: 計算結果の確認
if "!SIGNAL_DATE!"=="" (
    echo エラー: 日付の計算に失敗しました
    echo PowerShellが正常に動作していることを確認してください
    goto END
)

:: 日付形式の簡易チェック（8桁の数字かどうか）
echo !SIGNAL_DATE!| findstr /r "^[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]$" >nul
if errorlevel 1 (
    echo エラー: 計算された日付の形式が正しくありません: !SIGNAL_DATE!
    goto END
)

echo.
echo 実行パラメータ:
echo   売買シグナル日: !SIGNAL_DATE! (2週間前の日付を自動計算)
echo   評価日: 指定なし（実行時点の最新Close値を使用）
echo.
echo ====================================
echo 処理を開始します...
echo ====================================

:: Pythonスクリプトを実行
python evaluate_signals.py !SIGNAL_DATE!

:: 実行結果の確認
if errorlevel 1 (
    echo.
    echo ====================================
    echo エラーが発生しました
    echo ====================================
    echo Pythonスクリプトの実行中にエラーが発生しました。
    echo 以下の点を確認してください：
    echo - Pythonがインストールされているか
    echo - 必要なパッケージ（pandas, yfinance）がインストールされているか
    echo - InputDataフォルダにCSVファイルが存在するか
    echo - evaluate_signals.pyファイルが同じフォルダにあるか
    echo - 計算された日付（!SIGNAL_DATE!）が適切な営業日かどうか
) else (
    echo.
    echo ====================================
    echo 処理が正常に完了しました
    echo ====================================
    echo 結果はOutputフォルダに出力されています。
    echo 使用した売買シグナル日: !SIGNAL_DATE!
)

:END
echo.
echo 何かキーを押すとウィンドウが閉じます...
pause >nul