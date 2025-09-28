#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChartChecker - Stock Chart Generator with Custom Date Lines
Fetches stock data using yfinance and generates charts with reference date lines.
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

# Set up logging
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
    """Main class for generating stock charts with reference date lines."""
    
    def __init__(self, config_file: str = 'config.ini'):
        """Initialize ChartChecker with configuration."""
        self.config = self._load_config(config_file)
        self.data_period_months = self.config.getint('CHART', 'data_period_months', fallback=6)
        self.output_dir = self.config.get('CHART', 'output_directory', fallback='output')
        self.chart_width = self.config.getfloat('CHART', 'chart_width', fallback=12.0)
        self.chart_height = self.config.getfloat('CHART', 'chart_height', fallback=8.0)
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set matplotlib to use Japanese fonts (suppress warnings)
        import warnings
        warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib.font_manager')
        plt.rcParams['font.family'] = ['DejaVu Sans', 'Meiryo', 'MS Gothic', 'Yu Gothic']
    
    def _load_config(self, config_file: str) -> configparser.ConfigParser:
        """Load configuration from INI file."""
        config = configparser.ConfigParser()
        if os.path.exists(config_file):
            config.read(config_file, encoding='utf-8')
        return config
    
    def load_input_csv(self, csv_file: str) -> pd.DataFrame:
        """Load input CSV file with ticker information."""
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
            required_columns = ['Ticker', '銘柄名', '基準日']
            
            # Check if all required columns exist
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Convert 基準日 to datetime
            df['基準日'] = pd.to_datetime(df['基準日'], errors='coerce')
            
            # Remove rows with invalid dates
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
        """Fetch stock data for the specified period."""
        try:
            # Calculate start and end dates
            end_date = reference_date + timedelta(days=30)  # 30 days after reference date
            start_date = reference_date - timedelta(days=self.data_period_months * 30)
            
            # Handle Japanese stock tickers (add .T suffix if not present)
            if self._is_japanese_ticker(ticker):
                if not ticker.endswith('.T'):
                    ticker_with_suffix = f"{ticker}.T"
                else:
                    ticker_with_suffix = ticker
                logger.info(f"Using Japanese ticker format: {ticker_with_suffix}")
            else:
                ticker_with_suffix = ticker
            
            # Fetch data using yfinance
            stock = yf.Ticker(ticker_with_suffix)
            data = stock.history(start=start_date, end=end_date)
            
            if data.empty:
                logger.warning(f"No data found for ticker {ticker} (tried as {ticker_with_suffix})")
                # Try alternative ticker formats for Japanese stocks
                if self._is_japanese_ticker(ticker) and not ticker.endswith('.T'):
                    alternative_ticker = f"{ticker}.TO"  # Try .TO suffix as well
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
            
            # Convert timezone-naive to timezone-aware if needed
            if data.index.tz is None:
                data.index = data.index.tz_localize('UTC')
            
            logger.info(f"Fetched {len(data)} data points for {ticker}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            logger.error(f"Tried ticker format: {ticker_with_suffix if 'ticker_with_suffix' in locals() else ticker}")
            return None
    
    def _is_japanese_ticker(self, ticker: str) -> bool:
        """Check if the ticker is a Japanese stock ticker."""
        # Remove .T suffix if present for checking
        clean_ticker = ticker.replace('.T', '')
        
        # Japanese stock tickers are typically 4 digits or 4 characters ending with A
        if len(clean_ticker) == 4:
            # Check if it's 4 digits (like 6946, 7203, etc.)
            if clean_ticker.isdigit():
                return True
            # Check if it ends with A (like 285A, 9984A, etc.)
            if clean_ticker.endswith('A'):
                return True
        return False
    
    def _plot_candlestick(self, ax, data, width=0.8):
        """Plot candlestick chart."""
        for i, (date, row) in enumerate(data.iterrows()):
            open_price = row['Open']
            close_price = row['Close']
            high_price = row['High']
            low_price = row['Low']
            
            # Determine color based on open vs close
            if close_price >= open_price:
                color = 'red'  # Bullish candle (red in Japanese style)
                body_color = 'red'  # Same color as border
            else:
                color = 'blue'  # Bearish candle (blue in Japanese style)
                body_color = 'blue'  # Same color as border
            
            # Plot high-low line
            ax.plot([i, i], [low_price, high_price], color=color, linewidth=1)
            
            # Plot open-close rectangle
            body_height = abs(close_price - open_price)
            body_bottom = min(open_price, close_price)
            
            if body_height > 0:
                # Draw body rectangle
                rect = Rectangle((i - width/2, body_bottom), width, body_height, 
                               facecolor=body_color, edgecolor=color, linewidth=1)
                ax.add_patch(rect)
            else:
                # Draw doji line
                ax.plot([i - width/2, i + width/2], [open_price, open_price], 
                       color=color, linewidth=2)
            
            # Draw open and close ticks
            ax.plot([i - width/2, i], [open_price, open_price], color=color, linewidth=2)
            ax.plot([i, i + width/2], [close_price, close_price], color=color, linewidth=2)
    
    def _plot_volume(self, ax, data, width=0.8):
        """Plot volume chart."""
        for i, (date, row) in enumerate(data.iterrows()):
            volume = row['Volume']
            open_price = row['Open']
            close_price = row['Close']
            
            # Determine color based on price movement
            if close_price >= open_price:
                color = 'red'  # Bullish volume
            else:
                color = 'blue'  # Bearish volume
            
            # Draw volume bar
            ax.bar(i, volume, width=width, color=color, alpha=0.7, edgecolor=color, linewidth=1)
    
    def create_chart(self, ticker: str, company_name: str, reference_date: datetime, 
                    stock_data: pd.DataFrame) -> str:
        """Create and save stock chart with reference date line."""
        try:
            # Create figure with two subplots (price chart and volume)
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(self.chart_width, self.chart_height), 
                                          gridspec_kw={'height_ratios': [3, 1]})
            
            # Plot candlestick chart on upper subplot
            self._plot_candlestick(ax1, stock_data)
            
            # Add reference date line between candles
            # Find the closest date in the data to the reference date
            ref_date_idx = None
            min_diff = float('inf')
            
            # Ensure reference_date is timezone-aware
            if reference_date.tzinfo is None:
                reference_date = reference_date.replace(tzinfo=stock_data.index.tz)
            
            for i, date in enumerate(stock_data.index):
                diff = abs((date - reference_date).total_seconds())
                if diff < min_diff:
                    min_diff = diff
                    ref_date_idx = i
            
            if ref_date_idx is not None:
                # Position the line between the reference date candle and the previous candle
                line_position = ref_date_idx - 0.5
                ax1.axvline(x=line_position, color='green', linestyle='--', linewidth=2, 
                           label=f'基準日: {reference_date.strftime("%Y-%m-%d")}')
            
            # Customize price chart
            ax1.set_title(f'{company_name} ({ticker}) - ローソク足チャート', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Price', fontsize=12)
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Set y-axis format for price
            ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}'))
            
            # Plot volume chart on lower subplot
            self._plot_volume(ax2, stock_data)
            
            # Set x-axis labels for both subplots
            # Sample every nth date to avoid overcrowding
            n = max(1, len(stock_data) // 10)
            x_positions = range(0, len(stock_data), n)
            x_labels = [stock_data.index[i].strftime('%Y-%m-%d') for i in x_positions]
            
            ax1.set_xticks(x_positions)
            ax1.set_xticklabels([])  # Remove x labels from upper chart
            ax2.set_xticks(x_positions)
            ax2.set_xticklabels(x_labels, rotation=45, ha='right')
            
            ax2.set_xlabel('Date', fontsize=12)
            ax2.set_ylabel('Volume', fontsize=12)
            ax2.grid(True, alpha=0.3)
            
            # Adjust layout
            plt.tight_layout()
            
            # Save chart
            filename = f"{ticker}_{company_name}_from{reference_date.strftime('%Y%m%d')}.png"
            filename = filename.replace('/', '_').replace('\\', '_')  # Clean filename
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
        """Process all stocks from the input CSV file."""
        try:
            # Load input data
            df = self.load_input_csv(csv_file)
            
            created_charts = []
            
            for index, row in df.iterrows():
                ticker = row['Ticker']
                company_name = row['銘柄名']
                reference_date = row['基準日']
                
                logger.info(f"Processing {ticker} - {company_name}")
                
                # Fetch stock data
                stock_data = self.fetch_stock_data(ticker, reference_date)
                
                if stock_data is not None:
                    # Create chart
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
    """Main function."""
    parser = argparse.ArgumentParser(description='Generate stock charts with reference date lines')
    parser.add_argument('--input', '-i', default='Input.csv', 
                       help='Input CSV file (default: Input.csv)')
    parser.add_argument('--config', '-c', default='config.ini',
                       help='Configuration file (default: config.ini)')
    
    args = parser.parse_args()
    
    try:
        # Initialize ChartChecker
        checker = ChartChecker(args.config)
        
        # Process all stocks
        created_charts = checker.process_all_stocks(args.input)
        
        print(f"\n=== Chart Generation Complete ===")
        print(f"Created {len(created_charts)} charts in '{checker.output_dir}' directory")
        
        if created_charts:
            print("\nCreated charts:")
            for chart in created_charts:
                print(f"  - {chart}")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
