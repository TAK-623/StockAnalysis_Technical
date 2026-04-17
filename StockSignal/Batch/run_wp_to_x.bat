@echo off
cd /d %~dp0..
chcp 65001 > nul
echo WordPressの記事をXへ投稿します...
python ..\X_twitter\post_wp_to_x.py
if %ERRORLEVEL% NEQ 0 (
    echo エラーが発生しました。
    pause
    exit /b 1
)
echo 完了しました。
pause
