#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChartChecker - 基準日線付き株式チャート生成ツール
yfinanceを使用して株式データを取得し、基準日線付きチャートを生成します。
"""

import os
import sys
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import argparse
import logging
from typing import List, Dict, Optional
import configparser
from matplotlib.patches import Rectangle
import numpy as np

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chart_checker.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ChartChecker:
    """基準日線付き株式チャート生成のメインクラス"""
    
    def __init__(self, config_file: str = 'config.ini'):
        """設定ファイルでChartCheckerを初期化"""
        self.config = self._load_config(config_file)
        self.data_period_months = self.config.getint('CHART', 'data_period_months', fallback=6)
        self.output_dir = self.config.get('CHART', 'output_directory', fallback='output')
        self.chart_width = self.config.getfloat('CHART', 'chart_width', fallback=12.0)
        self.chart_height = self.config.getfloat('CHART', 'chart_height', fallback=8.0)
        
        # 出力ディレクトリが存在しない場合は作成
        os.makedirs(self.output_dir, exist_ok=True)
        
        # matplotlibで日本語フォントを使用（警告を抑制）
        import warnings
        warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib.font_manager')
        plt.rcParams['font.family'] = ['DejaVu Sans', 'Meiryo', 'MS Gothic', 'Yu Gothic']
    
    def _load_config(self, config_file: str) -> configparser.ConfigParser:
        """INIファイルから設定を読み込み"""
        config = configparser.ConfigParser()
        if os.path.exists(config_file):
            config.read(config_file, encoding='utf-8')
        return config
    
    def load_input_csv(self, csv_file: str) -> pd.DataFrame:
        """ティッカー情報を含む入力CSVファイルを読み込み"""
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
            required_columns = ['Ticker', '銘柄名', '基準日']
            
            # 必要な列がすべて存在するかチェック
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # 基準日を日時型に変換
            df['基準日'] = pd.to_datetime(df['基準日'], errors='coerce')
            
            # 無効な日付の行を削除
            invalid_dates = df['基準日'].isna()
            if invalid_dates.any():
                logger.warning(f"Removing {invalid_dates.sum()} rows with invalid dates")
                df = df[~invalid_dates]
            
            logger.info(f"Loaded {len(df)} valid entries from {csv_file}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading CSV file {csv_file}: {e}")
            raise
    
    def fetch_stock_data(self, ticker: str, reference_date: datetime) -> Optional[pd.DataFrame]:
        """指定期間の株式データを取得"""
        try:
            # 開始日と終了日を計算
            end_date = reference_date + timedelta(days=30)  # 基準日から30日後
            start_date = reference_date - timedelta(days=self.data_period_months * 30)
            
            # 日本の株式ティッカーを処理（.Tサフィックスがない場合は追加）
            if self._is_japanese_ticker(ticker):
                if not ticker.endswith('.T'):
                    ticker_with_suffix = f"{ticker}.T"
                else:
                    ticker_with_suffix = ticker
                logger.info(f"Using Japanese ticker format: {ticker_with_suffix}")
            else:
                ticker_with_suffix = ticker
            
            # yfinanceを使用してデータを取得
            stock = yf.Ticker(ticker_with_suffix)
            data = stock.history(start=start_date, end=end_date)
            
            if data.empty:
                logger.warning(f"No data found for ticker {ticker} (tried as {ticker_with_suffix})")
                # 日本の株式の代替ティッカーフォーマットを試行
                if self._is_japanese_ticker(ticker) and not ticker.endswith('.T'):
                    alternative_ticker = f"{ticker}.TO"  # .TOサフィックスも試行
                    logger.info(f"Trying alternative format: {alternative_ticker}")
                    stock_alt = yf.Ticker(alternative_ticker)
                    data = stock_alt.history(start=start_date, end=end_date)
                    if not data.empty:
                        logger.info(f"Found data with .TO suffix for {ticker}")
                    else:
                        logger.warning(f"No data found with alternative format either")
                        return None
                else:
                    return None
            
            # タイムゾーン情報がない場合は追加
            if data.index.tz is None:
                data.index = data.index.tz_localize('UTC')
            
            logger.info(f"Fetched {len(data)} data points for {ticker}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            logger.error(f"Tried ticker format: {ticker_with_suffix if 'ticker_with_suffix' in locals() else ticker}")
            return None
    
    def _is_japanese_ticker(self, ticker: str) -> bool:
        """ティッカーが日本の株式ティッカーかどうかをチェック"""
        # チェック用に.Tサフィックスを削除
        clean_ticker = ticker.replace('.T', '')
        
        # 日本の株式ティッカーは通常4桁数字または4文字でAで終わる
        if len(clean_ticker) == 4:
            # 4桁数字かチェック（例：6946, 7203など）
            if clean_ticker.isdigit():
                return True
            # Aで終わるかチェック（例：285A, 9984Aなど）
            if clean_ticker.endswith('A'):
                return True
        return False
    
    def _plot_candlestick(self, ax, data, width=0.8):
        """ローソク足チャートを描画"""
        for i, (date, row) in enumerate(data.iterrows()):
            open_price = row['Open']
            close_price = row['Close']
            high_price = row['High']
            low_price = row['Low']
            
            # 始値と終値に基づいて色を決定
            if close_price >= open_price:
                color = 'red'  # 陽線（日本のスタイルでは赤）
                body_color = 'red'  # 枠線と同じ色
            else:
                color = 'blue'  # 陰線（日本のスタイルでは青）
                body_color = 'blue'  # 枠線と同じ色
            
            # 高値-安値線を描画
            ax.plot([i, i], [low_price, high_price], color=color, linewidth=1)
            
            # 始値-終値の矩形を描画
            body_height = abs(close_price - open_price)
            body_bottom = min(open_price, close_price)
            
            if body_height > 0:
                # 実体の矩形を描画
                rect = Rectangle((i - width/2, body_bottom), width, body_height, 
                               facecolor=body_color, edgecolor=color, linewidth=1)
                ax.add_patch(rect)
            else:
                # ドジ線を描画
                ax.plot([i - width/2, i + width/2], [open_price, open_price], 
                       color=color, linewidth=2)
            
            # 始値と終値の目盛りを描画
            ax.plot([i - width/2, i], [open_price, open_price], color=color, linewidth=2)
            ax.plot([i, i + width/2], [close_price, close_price], color=color, linewidth=2)
    
    def _plot_volume(self, ax, data, width=0.8):
        """出来高チャートを描画"""
        for i, (date, row) in enumerate(data.iterrows()):
            volume = row['Volume']
            open_price = row['Open']
            close_price = row['Close']
            
            # 価格変動に基づいて色を決定
            if close_price >= open_price:
                color = 'red'  # 陽線の出来高
            else:
                color = 'blue'  # 陰線の出来高
            
            # 出来高バーを描画
            ax.bar(i, volume, width=width, color=color, alpha=0.7, edgecolor=color, linewidth=1)
    
    def create_chart(self, ticker: str, company_name: str, reference_date: datetime, 
                    stock_data: pd.DataFrame) -> str:
        """基準日線付き株式チャートを作成して保存"""
        try:
            # 2つのサブプロット（価格チャートと出来高）で図を作成
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(self.chart_width, self.chart_height), 
                                          gridspec_kw={'height_ratios': [3, 1]})
            
            # 上部サブプロットにローソク足チャートを描画
            self._plot_candlestick(ax1, stock_data)
            
            # ローソク足の間に基準日線を追加
            # データ内で基準日に最も近い日付を見つける
            ref_date_idx = None
            min_diff = float('inf')
            
            # 基準日がタイムゾーン情報を持つようにする
            if reference_date.tzinfo is None:
                reference_date = reference_date.replace(tzinfo=stock_data.index.tz)
            
            for i, date in enumerate(stock_data.index):
                diff = abs((date - reference_date).total_seconds())
                if diff < min_diff:
                    min_diff = diff
                    ref_date_idx = i
            
            if ref_date_idx is not None:
                # 基準日のローソク足と前のローソク足の間に線を配置
                line_position = ref_date_idx - 0.5
                ax1.axvline(x=line_position, color='green', linestyle='--', linewidth=2, 
                           label=f'基準日: {reference_date.strftime("%Y-%m-%d")}')
            
            # 価格チャートをカスタマイズ
            ax1.set_title(f'{company_name} ({ticker}) - ローソク足チャート', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Price', fontsize=12)
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 価格のY軸フォーマットを設定
            ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}'))
            
            # 下部サブプロットに出来高チャートを描画
            self._plot_volume(ax2, stock_data)
            
            # 両方のサブプロットのX軸ラベルを設定
            # 過密を避けるためにn番目ごとの日付をサンプリング
            n = max(1, len(stock_data) // 10)
            x_positions = range(0, len(stock_data), n)
            x_labels = [stock_data.index[i].strftime('%Y-%m-%d') for i in x_positions]
            
            ax1.set_xticks(x_positions)
            ax1.set_xticklabels([])  # 上部チャートからXラベルを削除
            ax2.set_xticks(x_positions)
            ax2.set_xticklabels(x_labels, rotation=45, ha='right')
            
            ax2.set_xlabel('Date', fontsize=12)
            ax2.set_ylabel('Volume', fontsize=12)
            ax2.grid(True, alpha=0.3)
            
            # レイアウトを調整
            plt.tight_layout()
            
            # チャートを保存
            filename = f"{ticker}_{company_name}_from{reference_date.strftime('%Y%m%d')}.png"
            filename = filename.replace('/', '_').replace('\\', '_')  # ファイル名をクリーンアップ
            filepath = os.path.join(self.output_dir, filename)
            
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Chart saved: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error creating chart for {ticker}: {e}")
            plt.close()
            return None
    
    def process_all_stocks(self, csv_file: str) -> List[str]:
        """入力CSVファイルからすべての株式を処理"""
        try:
            # 入力データを読み込み
            df = self.load_input_csv(csv_file)
            
            created_charts = []
            
            for index, row in df.iterrows():
                ticker = row['Ticker']
                company_name = row['銘柄名']
                reference_date = row['基準日']
                
                logger.info(f"Processing {ticker} - {company_name}")
                
                # 株式データを取得
                stock_data = self.fetch_stock_data(ticker, reference_date)
                
                if stock_data is not None:
                    # チャートを作成
                    chart_path = self.create_chart(ticker, company_name, reference_date, stock_data)
                    if chart_path:
                        created_charts.append(chart_path)
                else:
                    logger.warning(f"Skipping {ticker} - no data available")
            
            logger.info(f"Successfully created {len(created_charts)} charts")
            return created_charts
            
        except Exception as e:
            logger.error(f"Error processing stocks: {e}")
            raise

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='基準日線付き株式チャートを生成')
    parser.add_argument('--input', '-i', default='Input.csv', 
                       help='入力CSVファイル (デフォルト: Input.csv)')
    parser.add_argument('--config', '-c', default='config.ini',
                       help='設定ファイル (デフォルト: config.ini)')
    
    args = parser.parse_args()
    
    try:
        # ChartCheckerを初期化
        checker = ChartChecker(args.config)
        
        # すべての株式を処理
        created_charts = checker.process_all_stocks(args.input)
        
        print(f"\n=== チャート生成完了 ===")
        print(f"'{checker.output_dir}' ディレクトリに {len(created_charts)} 個のチャートを作成しました")
        
        if created_charts:
            print("\n作成されたチャート:")
            for chart in created_charts:
                print(f"  - {chart}")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
