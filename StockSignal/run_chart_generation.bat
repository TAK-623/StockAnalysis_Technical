@echo off
echo 株価チャート生成とWordPress投稿を開始します...

cd /d "%~dp0"

REM Python環境の確認
python --version
if errorlevel 1 (
    echo Pythonがインストールされていません。
    pause
    exit /b 1
)

REM 必要なパッケージのインストール
echo 必要なパッケージをインストールしています...
pip install -r requirements.txt

REM メインスクリプトの実行
echo チャート生成とWordPress投稿を実行しています...
python main.py

if errorlevel 1 (
    echo エラーが発生しました。
    pause
    exit /b 1
) else (
    echo 処理が正常に完了しました。
)

pause

