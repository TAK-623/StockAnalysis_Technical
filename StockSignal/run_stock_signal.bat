@echo off
cd /d %~dp0
chcp 65001 > nul
echo 株価データ取得ツール（通常モード）を実行します...
python main.py
echo main.pyの処理が完了しました。
echo WordPressへのアップロードを開始します...
python Upload_WardPress.py
echo WordPressへのアップロードが完了しました。
echo Xへポストしています...
python ../X_twitter/post_wp_to_x.py
echo 一目均衡表情報のWordPressへのアップロードを開始します...
python Upload_WardPress_Ichimoku.py
echo 一目均衡表情報のWordPressへのアップロードが完了しました。
echo CSVファイルのアップロードを開始します...
python Upload_csv.py
echo Xへポストしています...
python ../X_twitter/post_wp_to_x.py
echo すべての処理が完了しました。
pause