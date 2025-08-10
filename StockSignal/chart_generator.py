"""
株価チャート生成モジュール

このモジュールは以下の機能を提供します：
1. Range_Brake.csvからレンジブレイク銘柄を読み込み
2. 各銘柄の株価データからチャートを生成
3. チャートに銘柄名とティッカーを表示
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
from datetime import datetime, timedelta
import japanize_matplotlib
import mplfinance as mpf
from matplotlib.ticker import FuncFormatter
from matplotlib import font_manager as fm

# 日本語フォント設定（Windowsで一般的なフォントを優先的に登録）
possible_fonts = [
    r"C:\\Windows\\Fonts\\meiryo.ttc",
    r"C:\\Windows\\Fonts\\meiryob.ttc",
    r"C:\\Windows\\Fonts\\msgothic.ttc",
    r"C:\\Windows\\Fonts\\YuGothM.ttc"
]
for fpath in possible_fonts:
    if os.path.exists(fpath):
        try:
            fm.fontManager.addfont(fpath)
        except Exception:
            pass
plt.rcParams['font.family'] = ['Meiryo', 'Yu Gothic', 'MS Gothic']

class ChartGenerator:
    """
    株価チャート生成クラス
    """
    
    def __init__(self):
        """
        初期化
        """
        # ファイルパスの設定
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.range_break_file = os.path.join(self.base_dir, "Result", "Range_Brake.csv")
        self.technical_signal_dir = os.path.join(self.base_dir, "TechnicalSignal")
        self.result_dir = os.path.join(self.base_dir, "Result")
        self.company_list_file = os.path.join(os.path.dirname(self.base_dir), "company_list_20250426.csv")
        
        # 銘柄名辞書の読み込み
        self.company_names = self._load_company_names()
        
        # チャートのスタイル設定
        plt.style.use('default')
        japanize_matplotlib.japanize()
    
    def _load_company_names(self):
        """
        銘柄名辞書を読み込み
        
        Returns:
            dict: ティッカーをキー、銘柄名を値とする辞書
        """
        try:
            df = pd.read_csv(self.company_list_file, encoding='utf-8')
            return dict(zip(df['Ticker'], df['銘柄名']))
        except Exception as e:
            print(f"銘柄名ファイルの読み込みエラー: {e}")
            return {}
    
    def load_range_break_tickers(self):
        """
        Range_Brake.csvからレンジブレイク銘柄のティッカーを読み込み
        
        Returns:
            list: レンジブレイク銘柄のティッカーリスト
        """
        try:
            df = pd.read_csv(self.range_break_file, encoding='utf-8')
            return df['Ticker'].tolist()
        except Exception as e:
            print(f"Range_Brake.csvの読み込みエラー: {e}")
            return []
    
    def load_stock_data(self, ticker):
        """
        指定されたティッカーの株価データを読み込み
        
        Args:
            ticker (str): ティッカー
            
        Returns:
            pandas.DataFrame: 株価データ（Date, Open, High, Low, Close, Volume）
        """
        try:
            signal_file = os.path.join(self.technical_signal_dir, f"{ticker}_signal.csv")
            if not os.path.exists(signal_file):
                print(f"信号ファイルが見つかりません: {signal_file}")
                return None
            
            df = pd.read_csv(signal_file, encoding='utf-8')
            
            # 必要な列のみを選択
            required_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in df.columns for col in required_columns):
                print(f"必要な列が見つかりません: {ticker}")
                return None
            
            # 日付列をdatetime型に変換
            df['Date'] = pd.to_datetime(df['Date'])
            
            # 最新のデータから過去60日分を取得
            df = df.sort_values('Date').tail(60)
            
            return df[required_columns]
            
        except Exception as e:
            print(f"株価データの読み込みエラー ({ticker}): {e}")
            return None
    
    def generate_chart(self, ticker):
        """
        指定されたティッカーのチャートを生成
        
        Args:
            ticker (str): ティッカー
            
        Returns:
            str: 生成されたチャートファイルのパス、失敗時はNone
        """
        try:
            # 株価データを読み込み
            df = self.load_stock_data(ticker)
            if df is None or df.empty:
                return None
            
            # 銘柄名を取得
            company_name = self.company_names.get(ticker, f"銘柄{ticker}")
            
            # mplfinance 用に整形
            df_mpf = df.copy()
            df_mpf = df_mpf.set_index('Date')
            df_mpf = df_mpf[['Open', 'High', 'Low', 'Close', 'Volume']]

            # 移動平均
            mav = (5, 25)

            # スタイル（フォント強制）
            mc = mpf.make_marketcolors(up='#d32f2f', down='#1e88e5', inherit=True)
            s = mpf.make_mpf_style(base_mpf_style='yahoo', marketcolors=mc, rc={'font.family': 'Meiryo'})

            output_file = os.path.join(self.result_dir, f"{ticker}_chart.png")

            # プロット（出来高付き、ローソク足）し、軸を調整
            fig, axes = mpf.plot(
                df_mpf,
                type='candle',
                mav=mav,
                volume=True,
                style=s,
                figsize=(12, 8),
                title=f"{ticker} - {company_name}",
                tight_layout=True,
                returnfig=True
            )

            # 出来高軸の指数表記を無効化、桁区切り
            if isinstance(axes, dict) and 'volume' in axes:
                axes['volume'].yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x):,}" if x >= 1 else f"{x}"))
            elif hasattr(axes, 'axes') and len(axes.axes) >= 2:
                vol_ax = axes.axes[-1]
                vol_ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x):,}" if x >= 1 else f"{x}"))

            fig.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close(fig)
            
            return output_file
            
        except Exception as e:
            print(f"チャート生成エラー ({ticker}): {e}")
            return None
