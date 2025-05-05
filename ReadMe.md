# 株価テクニカル指標分析システム

## 概要

このシステムは以下の機能を提供する：

1. 東証上場企業の株価データをYahoo Financeから取得
2. 取得した株価データに対して様々なテクニカル指標(移動平均線、MACD、RSI、RCI、一目均衡表など)を計算
3. テクニカル指標を基にした売買シグナルを生成
4. 生成したシグナルデータをCSVファイルとして保存
5. CSVファイルをGoogleドライブにアップロードし、Googleスプレッドシートに変換
6. 売買シグナル情報をWordPressサイトに自動投稿

## フォルダ構成

```
└── StockSignal/ (ルートディレクトリ)
    ├── main.py                                  # メイン実行スクリプト
    ├── config.py                                # システム設定ファイル
    ├── data_loader.py                           # データローディングモジュール
    ├── stock_fetcher.py                         # 株価データ取得モジュール
    ├── technical_indicators.py                  # 各種インジケーター演算＆売買シグナル生成モジュール
    ├── extract_signals.py                       # 売買シグナル抽出モジュール
    ├── Upload_csv.py                            # Googleドライブアップロードモジュール
    ├── Upload_WardPress.py                      # WordPress投稿モジュール
    ├── run_stock_signal.bat                     # 通常モード実行バッチファイル
    ├── run_stock_signal_test.bat                # テストモード実行バッチファイル
    ├── credentials.json                         # Google API認証情報
    ├── token.json                               # Google API認証トークン
    ├── company_list_20250228.csv                # 分析対象企業リスト
    ├── ReadMe.md                                # ドキュメント
    │
    ├── Data/                                    # 株価データ保存ディレクトリ
    │   └── [ticker].csv                         # 各銘柄の株価データCSV
    │
    ├── TechnicalSignal/                         # テクニカル指標分析結果
    │   ├── [ticker]_signal.csv                  # 各銘柄のシグナル状態CSV
    │   └── latest_signal.csv                    # 最新のシグナル状態を集約したCSV GoogleDriveにアップ
    │
    ├── Result/                                  # 分析結果出力ディレクトリ
    │   ├── signal_result_buy.csv                # 買いシグナル銘柄リスト WardPress・GoogleDriveにアップ
    │   └── signal_result_sell.csv               # 売りシグナル銘柄リスト WardPress・GoogleDriveにアップ
    │
    ├── Logs/                                    # ログファイル保存ディレクトリ
    │   └── stock_signal_YYYYMMDD.log            # 日付ごとのログファイル
    │
    ├── Test-BatchFiles/                         # テスト用の単体ファイル実行バッチ
    │   ├── single-test_run_Upload_csv.bat       # single-test_run_Upload_csv.pyの実行
    │   └── single-test_run_Upload_WardPress.bat # single-test_run_Upload_WardPress.pyの実行
    │
    ├── Test/                                    # テストモード用ディレクトリ
    │   ├── Data/                                # テスト用データ保存
    │   ├── TechnicalSignal/                     # テスト用分析結果
    │   ├── Result/                              # テスト用出力結果
    │   ├── Logs/                                # テスト用ログ
    │   └── company_list_20250228_test.csv       # テスト用対象企業リスト
    │
    └── Tools/                                   # 関連ツール
        └── MakeCompanyList/                     # CompanyListの整形ツール
            ├── make_company_indusrty_list.bat            # Pythonスクリプト実行用のバッチファイル
            └── make_company_indusrty_list.py             # 整形実行スクリプト
```

## システム構成

### メインモジュール

- `main.py` - システム全体の実行エントリーポイント
- `run_stock_signal.bat` - 通常モードで実行するためのバッチファイル
- `run_stock_signal_test.bat` - テストモードで実行するためのバッチファイル

### データ取得・分析モジュール

- `stock_fetcher.py` - Yahoo Finance APIを使用して株価データを取得
- `technical_indicators.py` - テクニカル指標の計算処理、売買シグナルの生成と分析、シグナル変化の検出処理

### データ出力モジュール

- `extract_signals.py` - 買い/売りシグナルの抽出と保存
- `Upload_csv.py` - 分析結果をGoogleドライブにアップロード
- `Upload_WardPress.py` - 分析結果をWordPressに投稿

### 共通・設定モジュール

- `config.py` - システム全体の設定値を管理
- `data_loader.py` - 企業リストの読み込みとロガー設定

## 実行方法

### 通常モード実行

```
run_stock_signal.bat
```

このコマンドを実行すると以下の処理が順番に行われる：
1. 株価データの取得と分析
2. WordPressへの自動投稿
3. Googleドライブへのアップロード

### テストモード実行

```
run_stock_signal_test.bat
```

テストモードでは限定された銘柄のみを対象に処理を行い、結果は別のディレクトリに保存される。

## 設定

システムの設定は `config.py` で管理されている：

- ディレクトリパス設定
- 入出力ファイル設定
- 株価データ取得設定（期間、バッチサイズなど）
- テクニカル指標パラメータ設定

## テクニカル指標

以下のテクニカル指標を計算している：

1. **移動平均線 (MA)** - 5日、25日、75日
2. **MACD** - 短期12日、長期26日、シグナル9日
3. **RSI** - 短期9日、長期14日
4. **RCI (Rank Correlation Index)** - 短期9日、長期26日
5. **一目均衡表** - 転換線、基準線、先行スパンA/B、遅行線

## 売買シグナル生成ロジック

MACD&RSI買いシグナル条件：
- MACDがMACD_Signalを上回る（上昇モメンタム）
- 短期RSIが長期RSIを上回る（短期的な強さ）
- 長期RSIが40以下（まだ買われすぎではない）

MACD&RSI売りシグナル条件：
- MACDがMACD_Signalを下回る（下降モメンタム）
- 短期RSIが長期RSIを下回る（短期的な弱さ）
- 長期RSIが60以上（まだ売られすぎではない）

MACD&RCI買いシグナル条件：
- MACDがMACD_Signalを上回る（上昇モメンタム）
- 長期RCIが過去5営業日内に-80％を上回る

MACD&RCI売りシグナル条件：
- MACDがMACD_Signalを下回る（下降モメンタム）
- 長期RCIが過去5営業日内に80％を下回る

## Google API認証設定

Googleドライブへのアップロードを行うには以下の手順が必要：

1. `credentials.json` ファイルに適切なAPIキー情報を設定
2. 初回実行時にブラウザが開き、Googleアカウント認証を要求
3. 認証後、`token.json` が生成され、以降の認証に使用

エラー時のトラブルシューティング：
1. `token.json` を削除
2. `Upload_csv.py` を実行して再認証

## WordPressへの投稿

WordPressへの投稿には以下の情報が使用される：
- サイトURL: https://www.takstorage.site/
- 認証情報: アプリケーションパスワード方式

## TA-Libの更新方法

テクニカル指標計算に使用しているTA-Libを更新する場合：

1. [talib-build リリースページ](https://github.com/cgohlke/talib-build/releases)から適切なバージョンの.whlファイルをダウンロード
2. 以下のコマンドで更新：
   ```
   pip install ta_lib-*.*.*-cp311-cp311-win_amd64.whl
   ```

## 対象企業リスト

分析対象の企業リストは `company_list_20250228.csv` に含まれており、約3800社の東証上場企業が登録されている。
東証一部上場企業のリストは下記リンク先から取得する。
https://www.jpx.co.jp/markets/statistics-equities/misc/01.html