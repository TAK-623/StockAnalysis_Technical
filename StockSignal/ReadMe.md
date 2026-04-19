# StockSignal

株価データの取得からテクニカル分析、シグナル抽出、チャート生成、WordPress 投稿までを行う一連のツール群。

---

## 概要

本ツールは以下の処理を自動で実行する。

1. **株価データ取得**: yfinance API から複数銘柄の株価ヒストリカルデータを取得
2. **テクニカル指標計算**: 移動平均・RSI・MACD・RCI・一目均衡表などを計算
3. **シグナル抽出**: 条件に合致するブレイクアウト銘柄・押し目買い銘柄を抽出
4. **連続該当判定**: 前回結果と今回結果を比較し、連続該当銘柄に「◎」を付与
5. **ROE 情報付与**: 抽出結果に ROE 情報を自動付与
6. **チャート生成・WordPress 投稿**: 抽出銘柄のチャートを生成し WordPress へ投稿

---

## ディレクトリ構成 / 主要ファイル

```
StockSignal/
├── main.py                 # メインエントリ（取得〜抽出までを実行）
├── Upload_WardPress.py     # チャート生成＋WordPress 投稿
├── Upload_csv.py           # CSV アップロード系
├── config.py               # 設定値（バッチサイズ、待機時間、ディレクトリパス等）
├── data_loader.py          # ロガー設定＋企業リスト CSV 読み込み
├── stock_fetcher.py        # yfinance 経由の株価データ取得
├── technical_indicators.py # テクニカル指標の計算
├── signal_extractor.py     # ブレイクアウト・押し目銘柄の抽出（ROE 付与含む）
├── result_backup.py        # 前回結果のバックアップ＋連続該当判定
├── chart_generator.py      # チャート生成
├── run_stock_signal.bat    # 通常実行用バッチ
├── Batch/                  # その他バッチファイル（テスト・no-tweet 等）
├── Result/                 # 出力結果（Breakout.csv, push_mark.csv, チャート画像）
│   └── Previous/           # 前回結果のバックアップ
├── TechnicalSignal/        # 各銘柄のテクニカル指標 CSV
└── Test/                   # テストモード用の入出力
```

---

## 実行方法

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

主要ライブラリ: `pandas`, `numpy`, `yfinance`, `matplotlib`, `japanize-matplotlib`, `requests`

### 2. 通常実行

```bash
# 1) データ取得〜シグナル抽出
python main.py

# 2) チャート生成＋WordPress 投稿（連続該当判定含む）
python Upload_WardPress.py
```

バッチファイル経由でも実行可能:

```bash
run_stock_signal.bat
```

### 3. テストモード実行

少数銘柄で動作確認する場合は `--test` フラグを付けて実行する。
テストモードでは入出力が `StockSignal/Test/` 配下に切り替わる。

```bash
python main.py --test
```

---

## 機能詳細

### 1. シグナル抽出（ブレイクアウト・押し目）

`signal_extractor.py` が `TechnicalSignal/{Ticker}_signal.csv` を読み込み、
以下のシグナルを抽出して `Result/` に CSV 出力する。

- **ブレイクアウト銘柄** (`Breakout.csv`)
- **押し目買い銘柄** (`push_mark.csv`)

抽出条件の詳細は `signal_extractor.py` 内のコメントを参照。
条件を変更する場合もそのファイルを編集すればよい。

単独実行もサポート:

```bash
python signal_extractor.py --type breakout   # ブレイクアウトのみ
python signal_extractor.py --type push_mark  # 押し目のみ
python signal_extractor.py --type all        # 両方
```

---

### 2. ROE 情報の付与

`signal_extractor.py` 内の `get_roe_for_ticker()` が yfinance API から
ROE 情報を取得し、抽出結果の CSV およびチャート図の銘柄名に自動付与する。

- **取得方法**: `stock.info.get('returnOnEquity')` を使用（小数→パーセンテージに変換）
- **フォールバック**: `info` から取得できない場合は `financials` を参照。いずれも取得不可なら空欄
- **API 制限対策**: 銘柄間で 0.5 秒の待機時間を設定

チャート銘柄名の例:

```
160A - S: アズパートナーズ (ROE：29.24%)
7082 - G: ジモティー (ROE：38.04%)
```

`Breakout.csv` の列構成:

```
Ticker, Company, テーマ, 終値, ROE(%), BB上限(+2σ), 前日までの最高値, 上髭の長さ(%)
```

---

### 3. 連続該当判定（◎プレフィックス）

2 営業日連続で同じ銘柄がブレイクアウト／押し目に該当した場合、
チャート図と一覧の銘柄名先頭に「◎」を付与する機能。

`result_backup.py` が提供する 3 つの関数で実現する。

- `backup_previous_results()`: `main.py` 開始時に現在の結果を `Result/Previous/` へバックアップ
- `get_consecutive_tickers()`: 前回結果と今回結果の積集合で連続該当銘柄を特定
- `decorate_company_name()`: 連続該当銘柄の銘柄名先頭に「◎」を付与

**処理順序（重要）:**

1. `main.py` 開始時: 前回の `Result/Breakout.csv`・`push_mark.csv` を `Result/Previous/` へコピー
2. `main.py` 本処理: 新しい `Breakout.csv`・`push_mark.csv` を生成
3. `Upload_WardPress.py`: `Previous/` の前回結果と今回結果を比較し連続該当を判定、銘柄名を装飾

**注意:** 初回実行時は `Previous/` が空のため連続判定は行われない。

出力例（WordPress 記事内）:

```
◎ 日本アクア (ROE：21.04%)
◎ ジンジブ
◎ 高砂熱学工業 (ROE：20.16%)
```

---

### 4. チャート生成機能

`Upload_WardPress.py` がブレイク銘柄・押し目銘柄のチャートを生成し、
WordPress 記事に埋め込んで投稿する。

**仕様:**

- **対象銘柄**: `Breakout.csv` / `push_mark.csv` から最大 10 銘柄
- **期間**: 過去 60 日間の価格推移と出来高
- **表示要素**: 終値、高値・安値の範囲、5 日・25 日移動平均線、出来高
- **画像形式**: PNG（300dpi）
- **保存先**: `Result/{Ticker}_chart.png`
- **投稿方式**: Base64 エンコードで HTML に直接埋め込み
- **日本語対応**: `japanize-matplotlib` 使用

**カスタマイズ:**

- 対象銘柄数の変更 → `Upload_WardPress.py` の `range_break_tickers[:10]` を編集
- 表示期間の変更 → `load_stock_data` 内の `tail(60)` を編集
- チャートスタイルの変更 → `generate_chart` 関数を編集

---

## トラブルシューティング

### チャートが生成されない

1. 必要なパッケージがインストールされているか確認
2. `TechnicalSignal/` に該当銘柄の `{Ticker}_signal.csv` が存在するか確認
3. 企業リスト CSV（`config.COMPANY_LIST_FILE`）が存在するか確認

### ROE データが取得できない

1. インターネット接続を確認
2. `yfinance` ライブラリが最新か確認
3. 銘柄コード（`.T` サフィックス含む）が正しいか確認
4. 一部銘柄では取得不可のケースがある（空欄で処理継続）

### 処理が途中で停止する

1. ネットワーク接続を確認
2. yfinance の API レート制限の可能性 → 待機時間 (`config.TICKER_WAIT_TIME`) を増やす
3. 再実行を試行

### WordPress 投稿に失敗する

1. `wordpress_poster.py` の接続情報（URL、認証情報）を確認
2. 投稿先カテゴリ・タグの設定が有効か確認
3. 画像サイズが WordPress のアップロード上限を超えていないか確認

---

## 関連仕様

### 設定値（`config.py`）

- `BATCH_SIZE`: 株価取得のバッチサイズ
- `BATCH_WAIT_TIME` / `TICKER_WAIT_TIME`: API レート制限対策の待機秒数
- `HISTORY_PERIOD`: 取得期間（例: `"6mo"`）
- `RESULT_DIR` / `TEST_RESULT_DIR`: 結果の出力先
- `LOG_DIR` / `TEST_LOG_DIR`: ログ出力先
- `COMPANY_LIST_FILE` / `COMPANY_LIST_TEST_FILE`: 企業リスト CSV のファイル名
- `YF_SUFFIX`: Yahoo Finance 用のティッカーサフィックス（日本株は `.T`）

### ログファイル

- 通常モード: `config.LOG_DIR/{config.LOG_FILE_NAME}`
- テストモード: `config.TEST_LOG_DIR/{config.LOG_FILE_NAME}`

### バックアップファイル

- 前回結果: `StockSignal/Result/Previous/Breakout.csv`, `push_mark.csv`
- 実行のたびに `main.py` 開始時点で最新化される
