"""
設定ファイル - アプリケーションの設定値を管理します
"""
import os
from datetime import datetime, timedelta

# パス設定
BASE_DIR = "C:\\Users\\mount\\Git\\StockSignal"
TEST_DIR = os.path.join(BASE_DIR, "Test")

# ファイル設定
COMPANY_LIST_FILE = "company_list_20250228.csv"
COMPANY_LIST_TEST_FILE = "company_list_20250228_test.csv"

# 結果出力先
RESULT_DIR = os.path.join(BASE_DIR, "Result")
TEST_RESULT_DIR = os.path.join(TEST_DIR, "Result")

# テクニカル指標出力先
TECHNICAL_DIR = os.path.join(BASE_DIR, "TechnicalSignal")
TEST_TECHNICAL_DIR = os.path.join(TEST_DIR, "TechnicalSignal")

# 株価データ取得設定
BATCH_SIZE = 100  # 一度に取得する企業数
BATCH_WAIT_TIME = 5  # バッチ間の待機時間（秒）
TICKER_WAIT_TIME = 0.5  # 銘柄間の待機時間（秒）
HISTORY_PERIOD = "6mo"  # 取得期間（6ヶ月）

# ログ設定
LOG_DIR = os.path.join(BASE_DIR, "Logs")
TEST_LOG_DIR = os.path.join(TEST_DIR, "Logs")
LOG_FILE_NAME = f"stock_signal_{datetime.now().strftime('%Y%m%d')}.log"

# yfinance設定
YF_SUFFIX = ".T"  # 東証の銘柄コードの接尾辞

# テクニカル指標のパラメータ
# 移動平均線
MA_PERIODS = [5, 25, 75]

# MACD
MACD_FAST_PERIOD = 12
MACD_SLOW_PERIOD = 26
MACD_SIGNAL_PERIOD = 9

# RSI
RSI_SHORT_PERIOD = 9
RSI_LONG_PERIOD = 14

# RCI
RCI_SHORT_PERIOD = 9
RCI_LONG_PERIOD = 26

# 一目均衡表
ICHIMOKU_TENKAN_PERIOD = 9
ICHIMOKU_KIJUN_PERIOD = 26
ICHIMOKU_SENKOU_SPAN_B_PERIOD = 52
ICHIMOKU_DISPLACEMENT = 26

# 出力ファイル名
LATEST_SIGNAL_FILE = "latest_signal.csv"