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
└── StockSignal_Technical/ (ルートディレクトリ)
    ├── StockSignal
    │   ├── main.py                                     # メイン実行スクリプト
    │   ├── config.py                                   # システム設定ファイル
    │   ├── data_loader.py                              # データローディングモジュール
    │   ├── stock_fetcher.py                            # 株価データ取得モジュール
    │   ├── technical_indicators.py                     # 各種インジケーター演算＆売買シグナル生成モジュール
    │   ├── extract_signals.py                          # 売買シグナル抽出モジュール
    │   ├── Upload_csv.py                               # Googleドライブアップロードモジュール
    │   ├── Upload_WardPress.py                         # WordPress投稿モジュール
    │   ├── run_stock_signal.bat                        # 通常モード実行バッチファイル
    │   ├── run_stock_signal_test.bat                   # テストモード実行バッチファイル
    │   ├── run_stock_signal_no-tweet.bat               # 最後にツイートをしない通常モード実行バッチファイル
    │   │
    │   ├── TechnicalSignal/                            # テクニカル指標分析結果
    │   │   ├── [ticker]_signal.csv                     # 各銘柄のシグナル状態CSV
    │   │   └── latest_signal.csv                       # 最新のシグナル状態を集約したCSV GoogleDriveにアップ
    │   │
    │   ├── Test/                                       # テストモード用ディレクトリ
    │   │   ├── Data/                                   # テスト用データ保存
    │   │   ├── TechnicalSignal/                        # テスト用分析結果
    │   │   ├── Result/                                 # テスト用出力結果
    │   │   ├── Logs/                                   # テスト用ログ
    │   │   └── company_list_20250228_test.csv          # テスト用対象企業リスト
    │   │
    │   ├── Result/                                     # 分析結果出力ディレクトリ
    │   │   ├── signal_result_buy.csv                   # 買いシグナル銘柄リスト WardPress・GoogleDriveにアップ
    │   │   ├── signal_result_sell.csv                  # 売りシグナル銘柄リスト WardPress・GoogleDriveにアップ
    │   │   ├── strong_buying_trend.csv                 # 強気買いトレンド銘柄リスト WardPress・GoogleDriveにアップ
    │   │   └── strong_selling_trend.csv                # 強気売りトレンド銘柄リスト WardPress・GoogleDriveにアップ
    │   │
    │   └── Test-BatchFiles/                            # テスト用の単体ファイル実行バッチ
    │       ├── single-test_run_Upload_csv.bat           # single-test_run_Upload_csv.pyの実行
    │       └── single-test_run_Upload_WardPress.bat     # single-test_run_Upload_WardPress.pyの実行
    │
    ├── VolumeAnalysis/                                 # 出来高移動平均の算出
    │   ├── main.py                                     # メイン実行スクリプト
    │   ├── config.py                                   # システム設定ファイル
    │   ├── data_loader.py                              # データローディングモジュール
    │   ├── volume_analyzer.py                          # 出来高移動平均の算出スクリプト
    │   ├── Upload_csv.py                               # Googleドライブアップロードモジュール
    │   ├── Upload_WardPress.py                         # WordPress投稿モジュール
    │   ├── run_volume_analysis.bat                     # 通常モード実行バッチファイル
    │   ├── run_volume_analysis_test.bat                # テストモード実行バッチファイル
    │   ├── run_volume_analysis_no-tweet.bat            # 最後にツイートをしない通常モード実行バッチファイル
    │   │
    │   ├── output/
    │   │   ├── all_industries_volume_ma.csv            # 33業種の出来高移動平均情報
    │   │   ├── industries_volume_above_ma.csv          # 長期移動平均よりも短期移動平均の方が出来高が多い業種
    │   │   └── industries_volume_below_ma.csv          # 長期移動平均よりも短期移動平均の方が出来高が少ない業種
    │   │
    │   └── Test-BatchFiles/                            # テスト用の単体ファイル実行バッチ
    │       ├── single-test_run_Upload_csv.bat          # single-test_run_Upload_csv.pyの実行
    │       └── single-test_run_Upload_WardPress.bat    # single-test_run_Upload_WardPress.pyの実行
    │
    ├── credentials.json                                # Google API認証情報
    ├── token.json                                      # Google API認証トークン
    ├── company_list_20250228.csv                       # 分析対象企業リスト
    ├── ReadMe.md                                       # ドキュメント
    │
    ├── Data/                                           # 株価データ保存ディレクトリ
    │   └── [ticker].csv                                # 各銘柄の株価データCSV
    │
    ├── Logs/                                           # ログファイル保存ディレクトリ
    │   └── stock_signal_YYYYMMDD.log                   # 日付ごとのログファイル
    │
    └── Tools/                                          # 関連ツール
        ├── MakeCompanyList/                            # CompanyListの整形ツール
        │   ├── make_company_indusrty_list.bat          # Pythonスクリプト実行用のバッチファイル
        │   └── make_company_indusrty_list.py           # 整形実行スクリプト
        │
        └── Buy-Sell_Simulation/                        # 売買シグナルの評価ツール
            ├── InputData/                              # ツールの入力データ格納フォルダ
            ├── Output/                                 # ツールの出力データ格納ファルダ
            └── evaluate_signals.py                     # 売買シグナル評価ツール
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

### latest_signal.csvに出力されるテクニカル指標詳細

1. **移動平均線 (Moving Averages)**
   - **MA5**: 5日間の単純移動平均線
   - **MA25**: 25日間の単純移動平均線
   - **MA75**: 75日間の単純移動平均線
   - **MA5_Deviation**: MA5の乖離率 ((現在値-MA5)/MA5×100)
   - **MA5_Change**: MA5の前日比率
   - **MA25_Deviation**: MA25の乖離率
   - **MA25_Change**: MA25の前日比率
   - **MA75_Deviation**: MA75の乖離率
   - **MA75_Change**: MA75の前日比率

2. **MACD (Moving Average Convergence Divergence)**
   - **MACD**: MACD値 (短期EMA - 長期EMA)
   - **MACD_Signal**: MACDのシグナル線
   - **MACD_Hist**: MACDとシグナル線の差（ヒストグラム）

3. **RSI (Relative Strength Index)**
   - **RSI9**: 9日間の相対力指数
   - **RSI14**: 14日間の相対力指数
   - **RSI**: RSI14と同じ（後方互換性のため）

4. **RCI (Rank Correlation Index)**
   - **RCI9**: 9日間のランク相関指数
   - **RCI26**: 26日間のランク相関指数
   - **RCI_Short_Overbought**: RCI9が80以上の買われすぎ状態かどうか
   - **RCI_Short_Oversold**: RCI9が-80以下の売られすぎ状態かどうか
   - **RCI_Long_Overbought**: RCI26が80以上の買われすぎ状態かどうか
   - **RCI_Long_Oversold**: RCI26が-80以下の売られすぎ状態かどうか

5. **一目均衡表 (Ichimoku Kinko Hyo)**
   - **Ichimoku_Tenkan**: 転換線
   - **Ichimoku_Kijun**: 基準線
   - **Ichimoku_SenkouA**: 先行スパンA
   - **Ichimoku_SenkouB**: 先行スパンB
   - **Ichimoku_Chikou**: 遅行スパン
   - **Ichimoku_Above_Cloud**: 価格が雲の上にあるかどうか
   - **Ichimoku_Below_Cloud**: 価格が雲の下にあるかどうか
   - **Ichimoku_In_Cloud**: 価格が雲の中にあるかどうか
   - **Ichimoku_Cloud_Status**: 雲との関係（「雲の上」「雲の下」「雲の中」）
   - **Ichimoku_Chikou_Above_Price**: 遅行線が価格より上にあるかどうか
   - **Ichimoku_Chikou_Below_Price**: 遅行線が価格より下にあるかどうか
   - **Ichimoku_Tenkan_Above_Kijun**: 転換線が基準線より上にあるかどうか
   - **Ichimoku_Tenkan_Below_Kijun**: 転換線が基準線より下にあるかどうか
   - **SanYaku_Kouten**: 三役好転の基本条件を満たしているか
   - **SanYaku_Anten**: 三役暗転の基本条件を満たしているか
   - **Ichimoku_JudgeDate**: 判定日付
   - **Ichimoku_SanYaku**: 三役好転または三役暗転の状態

6. **基本価格データ**
   - **Open**: 始値
   - **High**: 高値
   - **Low**: 安値
   - **Close**: 終値
   - **Volume**: 出来高
   - **Dividends**: 配当
   - **Stock Splits**: 株式分割

7. **その他**
   - **Ticker**: 銘柄コード
   - **Company**: 会社名
   - **Capital Gains**: 評価益

## 売買シグナル生成ロジック

### latest_signal.csvに出力される売買シグナル詳細

1. **MACD-RSI シグナル**
   - **Buy シグナル条件**:
     - MACDがMACD_Signalを上回る（上昇モメンタム）
     - 短期RSI(RSI9)が長期RSI(RSI14)を上回る（短期的な強さ）
     - 長期RSI(RSI14)が40以下（まだ買われすぎではない）
   - **Sell シグナル条件**:
     - MACDがMACD_Signalを下回る（下降モメンタム）
     - 短期RSI(RSI9)が長期RSI(RSI14)を下回る（短期的な弱さ）
     - 長期RSI(RSI14)が60以上（まだ売られすぎではない）

2. **MACD-RCI シグナル**
   - **Buy シグナル条件**:
     - 直近5営業日内にRCI26が-80を上回る
     - MACDがMACD_Signalを上回る
     - RCI9(短期)が50以上
   - **Sell シグナル条件**:
     - 直近5営業日内にRCI26が80を下回る
     - MACDがMACD_Signalを下回る
     - RCI9(短期)が-50以下

3. **MA-Deviation シグナル** (移動平均線乖離率)
   - **Buy シグナル条件**:
     - 短期移動平均線の乖離率が-3%以下（売られすぎ）
     - 短期移動平均線の前日比率がプラス（上昇に転じている）
   - **Sell シグナル条件**:
     - 短期移動平均線の乖離率が3%以上（買われすぎ）
     - 短期移動平均線の前日比率がマイナス（下落に転じている）

4. **一目均衡表シグナル**
   - **三役好転シグナル**:
     - 価格が雲の上にある
     - 遅行線が価格より上にある
     - 転換線が基準線より上にある
   - **三役暗転シグナル**:
     - 価格が雲の下にある
     - 遅行線が価格より下にある
     - 転換線が基準線より下にある
5. **強気買いトレンド**
   - **条件**:
     - 前の営業日の短期移動平均と中期移動平均の差分よりも、最新の短期移動平均と中期移動平均の差分の方が大きい（上昇トレンドの加速）
     - 「短期移動平均 ＞ 中期移動平均 ＞ 長期移動平均」の関係が成立している（上昇トレンドの順序確認）
     - 最新のClose値が短期移動平均よりも高い（現在値がトレンドより強い）
   - **出力ファイル**: `strong_buying_trend.csv`

6. **強気売りトレンド**
   - **条件**:
     - 前の営業日の中期移動平均と短期移動平均の差分よりも、最新の中期移動平均と短期移動平均の差分の方が大きい（下降トレンドの加速）
     - 「短期移動平均 ＜ 中期移動平均 ＜ 長期移動平均」の関係が成立している（下降トレンドの順序確認）
     - 最新のClose値が短期移動平均よりも低い（現在値がトレンドより弱い）
   - **出力ファイル**: `strong_selling_trend.csv`

### 追加の抽出条件

extract_signals.py を使用して売買シグナルを抽出する際には、以下の追加条件も適用されます：

- **買いシグナル追加条件**:
  - CloseがHighとLowの中間よりも上にある（上髭が短い銘柄）
  
- **売りシグナル追加条件**:
  - CloseがHighとLowの中間よりも下にある（下髭が短い銘柄）

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

## 株価評価損益計算ツール

シグナル抽出モジュールで生成された売買シグナルの有効性を評価するためのツールです。このツールは`Tools/Buy-Sell_Simulation/evaluate_signals.py`に実装されています。

### 機能

- 指定した日付の翌営業日の株価と最新の株価を比較して評価損益を算出
- 複数の売買シグナルファイル形式に対応（MACD-RSI、MACD-RCI、レンジブレイク）
- 詳細な評価結果とサマリー情報を別々のCSVファイルに出力
- 買いシグナルと売りシグナルの正解率を自動判定

### 入力ファイル形式

以下のようなCSVファイルに対応しています：
1. 買いシグナル：`macd_rsi_signal_result_buy.csv`, `macd_rci_signal_result_buy.csv`
2. 売りシグナル：`macd_rsi_signal_result_sell.csv`, `macd_rci_signal_result_sell.csv`
3. レンジブレイク：`range_break.csv` または `Range_Brake.csv`

### 出力ファイル

1. 詳細評価結果：`{入力ファイル名}_eval.csv`
   - 銘柄コード、会社名
   - 評価額（最新のClose値 - 翌営業日のOpen値）
   - 評価損益率(%)
   - 売買の日、翌営業日のOpen値、最新のClose値など

2. サマリー情報：`summary_{指標タイプ}_{シグナルタイプ}.csv`
   - 合計評価額と評価損益率
   - シグナル正解率(%)
     - 買いシグナル：評価額がプラスの銘柄の割合
     - 売りシグナル：評価額がマイナスの銘柄の割合
   - 全体銘柄数と正解銘柄数

### 使用方法

1. ツールと同じフォルダに「InputData」フォルダを作成し、評価したいCSVファイルを配置
2. 「Output」フォルダを作成（存在しない場合は自動作成）
3. コマンドラインからスクリプトを実行：

```bash
python evaluate_signals.py 20240501 20250518
```

※「20240501」の部分には、評価したい日付をyyyymmdd形式で指定します。
※「20250518」の部分には、2025/5/18時点の株価情報を使用したい場合に指定します。指定しない場合、最新の株価情報を使用します。

### テクニカル指標と評価方法

このツールは以下のテクニカル指標に基づく売買シグナルを評価します：

1. **MACD-RSI シグナル**
   - 買いシグナル条件: MACDがMACD_Signalを上回る、RSI短期がRSI長期を上回る、RSI長期が40以下
   - 売りシグナル条件: MACDがMACD_Signalを下回る、RSI短期がRSI長期を下回る、RSI長期が60以上

2. **MACD-RCI シグナル**
   - 買いシグナル条件: 直近5営業日内にRCI26が-80を上回る、MACDがMACD_Signalを上回る、RCI9が50以上
   - 売りシグナル条件: 直近5営業日内にRCI26が80を下回る、MACDがMACD_Signalを下回る、RCI9が-50以下

3. **レンジブレイク シグナル**
   - 条件: 最新のCloseが直近1か月の前日までの最高値を更新、出来高増加、上髭短い

シグナルの正解判定：
- 買いシグナル：評価額がプラスなら正解
- 売りシグナル：評価額がマイナスなら正解