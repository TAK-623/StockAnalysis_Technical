# 概要
以下を実行する。
1. 東証一部上場企業の株価情報を取得し、テクニカル指標を算出する。
2. 算出して保存されたファイルをGoogleドライブにアップする。
3. 算出して保存されたファイルのうち、一目均衡表の情報はWardPressに自動投稿する。

# 上場企業リスト
東証一部上場企業のリストは下記リンク先から取得する。  
https://www.jpx.co.jp/markets/statistics-equities/misc/01.html

# Ta-Libの更新方法
TA-Libの更新が必要になった場合には、下記リンク先から”ta_lib-*.*.*-cp311-cp311-win_amd64.whl”をダウンロードし、  
.whlから更新のためのインストールを実行する。

## リンク先
https://github.com/cgohlke/talib-build/releases
## インストール時の実行コマンド
ダウンロードフォルダに.whlを置いた状態で下記を実行する。   
`pip install ta_lib-*.*.*-cp311-cp311-win_amd64.whl`

# トラブルシュート
## GoogleDriveへのアップロードが失敗しているとき
1. token.jsonを削除
2. cmdを開く
3. python Upload_csv.pyを実行して再認証