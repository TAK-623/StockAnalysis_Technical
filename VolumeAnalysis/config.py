import os

# テストモードの設定
TEST_MODE = False  # デフォルトは通常モード

# ファイルパスの設定
BASE_DIR = "C:\\Users\\mount\\Git\\StockAnalysis_Technical"
INPUT_FILE_PATH = os.path.join(BASE_DIR, "company_industry_list_20250426.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "VolumeAnalysis", "output")

# テストモード用の設定
TEST_TICKERS_COUNT = 5  # テストモードで使用する銘柄数

# 分析パラメータ
SHORT_TERM_PERIOD = 21  # 短期移動平均の期間（日数）
LONG_TERM_PERIOD = 126  # 長期移動平均の期間（日数）
STOCK_HISTORY_PERIOD = "1y"  # 株価データ取得期間

# 出力ファイル名
ALL_INDUSTRIES_FILE = "all_industries_volume_ma.csv"
ABOVE_MA_FILE = "industries_volume_above_ma.csv"
BELOW_MA_FILE = "industries_volume_below_ma.csv"

# テストモード時のファイル名
if TEST_MODE:
    ALL_INDUSTRIES_FILE = "test_" + ALL_INDUSTRIES_FILE
    ABOVE_MA_FILE = "test_" + ABOVE_MA_FILE
    BELOW_MA_FILE = "test_" + BELOW_MA_FILE