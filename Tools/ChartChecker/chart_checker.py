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
from typing import List, Dict, Optional, Tuple
import configparser
from matplotlib.patches import Rectangle
import numpy as np
import warnings

# 定数定義
class Constants:
    """アプリケーション全体で使用する定数"""
    
    # ファイル関連
    DEFAULT_CONFIG_FILE = 'config.ini'
    DEFAULT_INPUT_FILE = 'Input.csv'
    
    # CSV列名
    TICKER_COLUMN = 'Ticker'
    COMPANY_NAME_COLUMN = '銘柄名'
    REFERENCE_DATE_COLUMN = '基準日'
    
    # チャート設定
    CHART_DPI = 300
    
    # ローソク足設定
    CANDLESTICK_WIDTH = 0.8
    VOLUME_ALPHA = 0.7
    
    # 色設定
    BULLISH_COLOR = 'red'
    BEARISH_COLOR = 'blue'
    REFERENCE_LINE_COLOR = 'green'
    
    # 日本の株式ティッカー設定
    JAPANESE_TICKER_SUFFIX = '.T'
    JAPANESE_TICKER_ALTERNATIVE_SUFFIX = '.TO'
    JAPANESE_TICKER_LENGTH = 4

# ログ設定
def setup_logging() -> logging.Logger:
    """ログ設定を初期化"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('chart_checker.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class ConfigManager:
    """設定管理クラス"""
    
    def __init__(self, config_file: str = Constants.DEFAULT_CONFIG_FILE):
        self.config = self._load_config(config_file)
        self._setup_matplotlib()
    
    def _load_config(self, config_file: str) -> configparser.ConfigParser:
        """INIファイルから設定を読み込み"""
        config = configparser.ConfigParser()
        if os.path.exists(config_file):
            config.read(config_file, encoding='utf-8')
        return config
    
    def _setup_matplotlib(self) -> None:
        """matplotlibの設定を初期化"""
        warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib.font_manager')
        plt.rcParams['font.family'] = ['DejaVu Sans', 'Meiryo', 'MS Gothic', 'Yu Gothic']
    
    def get_data_period(self) -> str:
        """データ取得期間を取得
        
        config.iniの[CHART]セクションのdata_periodで設定可能
        - yfinanceのperiodパラメータの値を直接指定
        - デフォルト値：6mo
        - 使用可能な値：1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
        """
        return self.config.get('CHART', 'data_period', fallback='6mo')
    
    def get_output_dir(self) -> str:
        output_dir = self.config.get('CHART', 'output_directory', fallback='output')
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
    
    def get_chart_width(self) -> float:
        return self.config.getfloat('CHART', 'chart_width', fallback=12.0)
    
    def get_chart_height(self) -> float:
        return self.config.getfloat('CHART', 'chart_height', fallback=8.0)


class DataLoader:
    """データ読み込みクラス"""
    
    @staticmethod
    def load_input_csv(csv_file: str) -> pd.DataFrame:
        """ティッカー情報を含む入力CSVファイルを読み込み"""
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
            DataLoader._validate_csv_structure(df)
            df = DataLoader._clean_data(df)
            logger.info(f"Loaded {len(df)} valid entries from {csv_file}")
            return df
        except Exception as e:
            logger.error(f"Error loading CSV file {csv_file}: {e}")
            raise
    
    @staticmethod
    def _validate_csv_structure(df: pd.DataFrame) -> None:
        """CSVファイルの構造を検証"""
        required_columns = [Constants.TICKER_COLUMN, Constants.COMPANY_NAME_COLUMN, Constants.REFERENCE_DATE_COLUMN]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
    
    @staticmethod
    def _clean_data(df: pd.DataFrame) -> pd.DataFrame:
        """データをクリーニング"""
        # 基準日を日時型に変換
        df[Constants.REFERENCE_DATE_COLUMN] = pd.to_datetime(df[Constants.REFERENCE_DATE_COLUMN], errors='coerce')
        
        # 無効な日付の行を削除
        invalid_dates = df[Constants.REFERENCE_DATE_COLUMN].isna()
        if invalid_dates.any():
            logger.warning(f"Removing {invalid_dates.sum()} rows with invalid dates")
            df = df[~invalid_dates]
        
        return df


class StockDataFetcher:
    """株式データ取得クラス"""
    
    def __init__(self, data_period: str):
        self.data_period = data_period
    
    def fetch_stock_data(self, ticker: str, reference_date: datetime) -> Optional[pd.DataFrame]:
        """指定期間の株式データを取得
        
        取得するデータの期間：
        - yfinanceのperiodパラメータを使用（config.iniで設定可能）
        - デフォルト：6mo（6か月）
        - 使用可能な値：1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
        
        取得するデータ項目：
        - Open（始値）
        - High（高値）
        - Low（安値）
        - Close（終値）
        - Volume（出来高）
        
        日本の株式の場合：
        - 自動的に.Tサフィックスを追加
        - 取得できない場合は.TOサフィックスも試行
        
        注意：基準日はチャート上に縦線として表示されるが、データ取得期間には影響しない
        """
        try:
            ticker_with_suffix = self._format_ticker(ticker)
            stock_data = self._download_data(ticker_with_suffix, reference_date)
            
            if stock_data.empty:
                stock_data = self._try_alternative_format(ticker, reference_date)
            
            if stock_data is not None and not stock_data.empty:
                stock_data = self._normalize_timezone(stock_data)
                logger.info(f"Fetched {len(stock_data)} data points for {ticker}")
            
            return stock_data
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            return None
    
    def _format_ticker(self, ticker: str) -> str:
        """ティッカーを適切な形式にフォーマット"""
        if self._is_japanese_ticker(ticker):
            if not ticker.endswith(Constants.JAPANESE_TICKER_SUFFIX):
                ticker_with_suffix = f"{ticker}{Constants.JAPANESE_TICKER_SUFFIX}"
                logger.info(f"Using Japanese ticker format: {ticker_with_suffix}")
                return ticker_with_suffix
        return ticker
    
    def _download_data(self, ticker: str, reference_date: datetime) -> pd.DataFrame:
        """株価データをダウンロード
        取得期間の指定方法：
        - yfinanceのperiodパラメータを直接使用
        - config.iniで設定された期間値を使用
        """
        logger.info(f"データ取得期間: {self.data_period}")
        
        stock = yf.Ticker(ticker)
        return stock.history(period=self.data_period)
    
    def _try_alternative_format(self, ticker: str, reference_date: datetime) -> Optional[pd.DataFrame]:
        """代替フォーマットでデータ取得を試行"""
        if self._is_japanese_ticker(ticker) and not ticker.endswith(Constants.JAPANESE_TICKER_SUFFIX):
            alternative_ticker = f"{ticker}{Constants.JAPANESE_TICKER_ALTERNATIVE_SUFFIX}"
            logger.info(f"Trying alternative format: {alternative_ticker}")
            
            # 代替ティッカーでもperiodパラメータを使用
            stock = yf.Ticker(alternative_ticker)
            stock_data = stock.history(period=self.data_period)
            
            if not stock_data.empty:
                logger.info(f"Found data with {Constants.JAPANESE_TICKER_ALTERNATIVE_SUFFIX} suffix for {ticker}")
                return stock_data
        
        logger.warning(f"No data found for ticker {ticker}")
        return None
    
    def _normalize_timezone(self, data: pd.DataFrame) -> pd.DataFrame:
        """タイムゾーン情報を正規化"""
        if data.index.tz is None:
            data.index = data.index.tz_localize('UTC')
        return data
    
    @staticmethod
    def _is_japanese_ticker(ticker: str) -> bool:
        """ティッカーが日本の株式ティッカーかどうかをチェック"""
        clean_ticker = ticker.replace(Constants.JAPANESE_TICKER_SUFFIX, '')
        
        if len(clean_ticker) == Constants.JAPANESE_TICKER_LENGTH:
            return clean_ticker.isdigit() or clean_ticker.endswith('A')
        return False


class ChartChecker:
    """基準日線付き株式チャート生成のメインクラス"""
    
    def __init__(self, config_file: str = Constants.DEFAULT_CONFIG_FILE):
        """設定ファイルでChartCheckerを初期化"""
        self.config_manager = ConfigManager(config_file)
        self.data_loader = DataLoader()
        self.data_fetcher = StockDataFetcher(self.config_manager.get_data_period())
        self.output_dir = self.config_manager.get_output_dir()


class ChartRenderer:
    """チャート描画クラス"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
    
    def _plot_candlestick(self, ax, data: pd.DataFrame, width: float = Constants.CANDLESTICK_WIDTH) -> None:
        """ローソク足チャートを描画"""
        for i, (date, row) in enumerate(data.iterrows()):
            open_price = row['Open']
            close_price = row['Close']
            high_price = row['High']
            low_price = row['Low']
            
            color, body_color = self._get_candle_colors(close_price, open_price)
            
            # 高値-安値線を描画
            ax.plot([i, i], [low_price, high_price], color=color, linewidth=1)
            
            # 始値-終値の矩形を描画
            self._draw_candle_body(ax, i, open_price, close_price, color, body_color, width)
            
            # 始値と終値の目盛りを描画
            self._draw_candle_ticks(ax, i, open_price, close_price, color, width)
    
    def _get_candle_colors(self, close_price: float, open_price: float) -> Tuple[str, str]:
        """ローソク足の色を決定"""
        if close_price >= open_price:
            return Constants.BULLISH_COLOR, Constants.BULLISH_COLOR
        else:
            return Constants.BEARISH_COLOR, Constants.BEARISH_COLOR
    
    def _draw_candle_body(self, ax, i: int, open_price: float, close_price: float, 
                         color: str, body_color: str, width: float) -> None:
        """ローソク足の実体を描画"""
        body_height = abs(close_price - open_price)
        body_bottom = min(open_price, close_price)
        
        if body_height > 0:
            rect = Rectangle((i - width/2, body_bottom), width, body_height, 
                           facecolor=body_color, edgecolor=color, linewidth=1)
            ax.add_patch(rect)
        else:
            # ドジ線を描画
            ax.plot([i - width/2, i + width/2], [open_price, open_price], 
                   color=color, linewidth=2)
    
    def _draw_candle_ticks(self, ax, i: int, open_price: float, close_price: float, 
                          color: str, width: float) -> None:
        """ローソク足の目盛りを描画"""
        ax.plot([i - width/2, i], [open_price, open_price], color=color, linewidth=2)
        ax.plot([i, i + width/2], [close_price, close_price], color=color, linewidth=2)
    
    def _plot_volume(self, ax, data: pd.DataFrame, width: float = Constants.CANDLESTICK_WIDTH) -> None:
        """出来高チャートを描画"""
        for i, (date, row) in enumerate(data.iterrows()):
            volume = row['Volume']
            open_price = row['Open']
            close_price = row['Close']
            
            color = self._get_volume_color(close_price, open_price)
            ax.bar(i, volume, width=width, color=color, alpha=Constants.VOLUME_ALPHA, 
                  edgecolor=color, linewidth=1)
    
    def _get_volume_color(self, close_price: float, open_price: float) -> str:
        """出来高の色を決定"""
        return Constants.BULLISH_COLOR if close_price >= open_price else Constants.BEARISH_COLOR
    
    def _add_reference_line(self, ax, stock_data: pd.DataFrame, reference_date: datetime) -> None:
        """基準日線を追加"""
        ref_date_idx = self._find_closest_date_index(stock_data, reference_date)
        
        if ref_date_idx is not None:
            line_position = ref_date_idx - 0.5
            ax.axvline(x=line_position, color=Constants.REFERENCE_LINE_COLOR, 
                      linestyle='--', linewidth=2, 
                      label=f'基準日: {reference_date.strftime("%Y-%m-%d")}')
    
    def _find_closest_date_index(self, stock_data: pd.DataFrame, reference_date: datetime) -> Optional[int]:
        """基準日に最も近い日付のインデックスを見つける"""
        # 基準日がタイムゾーン情報を持つようにする
        if reference_date.tzinfo is None:
            reference_date = reference_date.replace(tzinfo=stock_data.index.tz)
        
        ref_date_idx = None
        min_diff = float('inf')
        
        for i, date in enumerate(stock_data.index):
            diff = abs((date - reference_date).total_seconds())
            if diff < min_diff:
                min_diff = diff
                ref_date_idx = i
        
        return ref_date_idx
    
    def _setup_chart_axes(self, ax1, ax2, stock_data: pd.DataFrame) -> None:
        """チャートの軸を設定"""
        # 両方のサブプロットのX軸ラベルを設定
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
    
    def create_chart(self, ticker: str, company_name: str, reference_date: datetime, 
                    stock_data: pd.DataFrame, output_dir: str) -> Optional[str]:
        """基準日線付き株式チャートを作成して保存"""
        try:
            # 2つのサブプロット（価格チャートと出来高）で図を作成
            fig, (ax1, ax2) = plt.subplots(2, 1, 
                                          figsize=(self.config_manager.get_chart_width(), 
                                                  self.config_manager.get_chart_height()), 
                                          gridspec_kw={'height_ratios': [3, 1]})
            
            # 上部サブプロットにローソク足チャートを描画
            self._plot_candlestick(ax1, stock_data)
            
            # 基準日線を追加
            self._add_reference_line(ax1, stock_data, reference_date)
            
            # 価格チャートをカスタマイズ
            ax1.set_title(f'{company_name} ({ticker}) - ローソク足チャート', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Price', fontsize=12)
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}'))
            
            # 下部サブプロットに出来高チャートを描画
            self._plot_volume(ax2, stock_data)
            
            # チャートの軸を設定
            self._setup_chart_axes(ax1, ax2, stock_data)
            
            # レイアウトを調整
            plt.tight_layout()
            
            # チャートを保存
            filename = f"{ticker}_{company_name}_from{reference_date.strftime('%Y%m%d')}.png"
            filename = filename.replace('/', '_').replace('\\', '_')  # ファイル名をクリーンアップ
            filepath = os.path.join(output_dir, filename)
            
            plt.savefig(filepath, dpi=Constants.CHART_DPI, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Chart saved: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error creating chart for {ticker}: {e}")
            plt.close()
            return None


class ChartChecker:
    """基準日線付き株式チャート生成のメインクラス"""
    
    def __init__(self, config_file: str = Constants.DEFAULT_CONFIG_FILE):
        """設定ファイルでChartCheckerを初期化"""
        self.config_manager = ConfigManager(config_file)
        self.data_loader = DataLoader()
        self.data_fetcher = StockDataFetcher(self.config_manager.get_data_period())
        self.chart_renderer = ChartRenderer(self.config_manager)
        self.output_dir = self.config_manager.get_output_dir()
    
    def process_all_stocks(self, csv_file: str) -> List[str]:
        """入力CSVファイルからすべての株式を処理
        
        処理の流れ：
        1. CSVファイルから銘柄情報を読み込み
        2. 各銘柄について以下を実行：
           - 処理実行時点から指定した期間の株式データを取得（config.iniで設定可能）
           - 処理実行時点（今日）までのデータを取得
           - ローソク足チャートと出来高チャートを生成
           - 基準日線をチャートに描画
           - PNGファイルとして保存
        """
        try:
            # 入力データを読み込み
            df = self.data_loader.load_input_csv(csv_file)
            
            created_charts = []
            
            for index, row in df.iterrows():
                ticker = row[Constants.TICKER_COLUMN]
                company_name = row[Constants.COMPANY_NAME_COLUMN]
                reference_date = row[Constants.REFERENCE_DATE_COLUMN]
                
                logger.info(f"Processing {ticker} - {company_name}")
                
                # 株式データを取得（処理実行時点から過去Nか月分のデータ）
                stock_data = self.data_fetcher.fetch_stock_data(ticker, reference_date)
                
                if stock_data is not None:
                    # ローソク足チャートと出来高チャートを作成
                    chart_path = self.chart_renderer.create_chart(
                        ticker, company_name, reference_date, stock_data, self.output_dir)
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
    parser.add_argument('--input', '-i', default=Constants.DEFAULT_INPUT_FILE, 
                       help=f'入力CSVファイル (デフォルト: {Constants.DEFAULT_INPUT_FILE})')
    parser.add_argument('--config', '-c', default=Constants.DEFAULT_CONFIG_FILE,
                       help=f'設定ファイル (デフォルト: {Constants.DEFAULT_CONFIG_FILE})')
    
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
