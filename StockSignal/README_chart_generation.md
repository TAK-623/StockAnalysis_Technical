# 株価チャート生成とWordPress投稿機能

この機能は、レンジブレイク銘柄の株価チャートを自動生成し、WordPressに投稿する機能を提供します。

## 機能概要

1. **Range_Brake.csvの読み込み**: StockSignal/ResultフォルダのRange_Brake.csvからレンジブレイク銘柄を読み込み
2. **チャート生成**: 各銘柄の株価データから過去60日間のチャートを生成
3. **WordPress投稿**: 生成したチャートをWordPress記事に投稿

## ファイル構成

```
StockSignal/
├── main.py                    # メイン実行ファイル
├── chart_generator.py         # チャート生成モジュール
├── wordpress_poster.py        # WordPress投稿モジュール
├── requirements.txt           # 必要な依存関係
├── run_chart_generation.bat   # 実行用バッチファイル
└── README_chart_generation.md # このファイル
```

## 必要な環境

- Python 3.7以上
- 以下のPythonパッケージ:
  - pandas
  - matplotlib
  - japanize-matplotlib
  - requests
  - numpy

## 使用方法

### 1. 自動実行（推奨）

`run_chart_generation.bat` をダブルクリックして実行します。

### 2. 手動実行

```bash
cd StockSignal
pip install -r requirements.txt
python main.py
```

## 処理の流れ

1. **Range_Brake.csvの読み込み**
   - StockSignal/Result/Range_Brake.csvからレンジブレイク銘柄のティッカーを取得

2. **株価データの読み込み**
   - StockSignal/TechnicalSignal/{Ticker}_signal.csvから各銘柄の株価データを取得
   - 必要な列: Date, Open, High, Low, Close, Volume

3. **チャート生成**
   - 過去60日間の価格推移と出来高を表示
   - 5日・25日移動平均線を追加
   - 銘柄名とティッカーをタイトルに表示
   - StockSignal/Result/{Ticker}_chart.pngとして保存

4. **WordPress投稿**
   - レンジブレイク銘柄一覧テーブルを生成
   - 各銘柄のチャート画像をbase64エンコードしてHTMLに埋め込み
   - WordPressに自動投稿

## 出力ファイル

- **チャート画像**: StockSignal/Result/{Ticker}_chart.png
- **WordPress記事**: レンジブレイク銘柄チャート_{日付} として投稿

## エラーハンドリング

- 株価データが見つからない銘柄はスキップ
- チャート生成に失敗した銘柄はスキップ
- エラーメッセージをコンソールに出力

## カスタマイズ

### チャートの期間変更

`chart_generator.py` の `load_stock_data` メソッドで以下の行を変更:

```python
# 最新のデータから過去60日分を取得
df = df.sort_values('Date').tail(60)  # 60を変更
```

### チャートのスタイル変更

`chart_generator.py` の `generate_chart` メソッドでチャートの見た目をカスタマイズできます。

### WordPress投稿設定

`wordpress_poster.py` の `__init__` メソッドでWordPressの接続情報を変更できます。

## 注意事項

- 初回実行時は必要なパッケージのインストールに時間がかかる場合があります
- 大量の銘柄がある場合、チャート生成に時間がかかる可能性があります
- WordPressの接続情報は適切に管理してください

