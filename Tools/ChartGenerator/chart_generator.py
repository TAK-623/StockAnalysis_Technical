#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
チャート生成ツール
指定した銘柄のチャート図を生成するツール
"""

import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from datetime import datetime
import os
import sys
import warnings

# Completely suppress matplotlib font warnings
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend to avoid font issues

# Simple font configuration
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class ChartGenerator:
    def __init__(self):
        self.output_dir = "output"
        self.periods = {
            "1mo": "1 month",
            "3mo": "3 months", 
            "6mo": "6 months",
            "1y": "1 year",
            "2y": "2 years",
            "5y": "5 years",
            "10y": "10 years",
            "ytd": "Year to date",
            "max": "Maximum period"
        }
        
        # 出力ディレクトリの作成
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def get_user_input(self):
        """Get user input"""
        print("=== Chart Generator Tool ===")
        print()
        
        # Ticker input
        while True:
            ticker = input("Enter Ticker (4-digit number): ").strip()
            if ticker.isdigit() and len(ticker) == 4:
                break
            else:
                print("Error: Please enter a 4-digit number.")
        
        # Period selection
        print("\nSelect period:")
        for i, (key, value) in enumerate(self.periods.items(), 1):
            print(f"{i}. {key} ({value})")
        
        while True:
            try:
                choice = int(input("\nEnter selection number (1-9): "))
                if 1 <= choice <= 9:
                    period_key = list(self.periods.keys())[choice - 1]
                    break
                else:
                    print("Error: Please enter a number between 1-9.")
            except ValueError:
                print("Error: Please enter a number.")
        
        return ticker, period_key
    
    def fetch_stock_data(self, ticker, period):
        """株価データを取得"""
        try:
            # 日本株の場合は.Tを付ける
            symbol = f"{ticker}.T"
            stock = yf.Ticker(symbol)
            
            print(f"Fetching data... ({ticker})")
            data = stock.history(period=period)
            
            if data.empty:
                raise ValueError(f"Failed to fetch data: {ticker}")
            
            # 銘柄名を取得
            try:
                company_name = stock.info.get('longName', '')
                if not company_name:
                    company_name = stock.info.get('shortName', '')
                if not company_name:
                    company_name = f"Ticker_{ticker}"
            except:
                company_name = f"Ticker_{ticker}"
            
            return data, company_name
            
        except Exception as e:
            print(f"Error: Failed to fetch data - {e}")
            return None, None
    
    def calculate_moving_averages(self, data):
        """移動平均を計算"""
        data['MA5'] = data['Close'].rolling(window=5).mean()
        data['MA25'] = data['Close'].rolling(window=25).mean()
        data['MA75'] = data['Close'].rolling(window=75).mean()
        data['MA200'] = data['Close'].rolling(window=200).mean()
        return data
    
    def create_chart(self, data, ticker, period, company_name):
        """チャートを作成"""
        # 移動平均を計算
        data = self.calculate_moving_averages(data)
        
        # 図のサイズ設定
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), 
                                      gridspec_kw={'height_ratios': [3, 1]})
        
        # ローソク足チャート
        self.plot_candlestick(ax1, data, ticker, company_name)
        
        # 移動平均線
        self.plot_moving_averages(ax1, data)
        
        # 出来高チャート
        self.plot_volume(ax2, data)
        
        # レイアウト調整
        plt.tight_layout()
        
        # ファイル保存（銘柄名と実行日を含む）
        # 銘柄名をファイル名に使用可能な形式に変換
        safe_company_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_company_name = safe_company_name.replace(' ', '_')
        
        # 現在の日付を取得
        current_date = datetime.now().strftime('%Y%m%d')
        
        filename = f"{ticker}_{safe_company_name}_chart_{period}_{current_date}.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Chart saved: {filepath}")
        return filepath
    
    def plot_candlestick(self, ax, data, ticker, company_name):
        """ローソク足を描画"""
        # 上昇・下降の判定
        up = data[data['Close'] >= data['Open']]
        down = data[data['Close'] < data['Open']]
        
        # 上昇時のローソク足（赤）
        if not up.empty:
            ax.bar(up.index, up['Close'] - up['Open'], bottom=up['Open'], 
                   color='red', alpha=0.7, width=0.8)
            ax.bar(up.index, up['High'] - up['Close'], bottom=up['Close'], 
                   color='red', alpha=0.7, width=0.1)
            ax.bar(up.index, up['Low'] - up['Open'], bottom=up['Open'], 
                   color='red', alpha=0.7, width=0.1)
        
        # 下降時のローソク足（青）
        if not down.empty:
            ax.bar(down.index, down['Close'] - down['Open'], bottom=down['Open'], 
                   color='blue', alpha=0.7, width=0.8)
            ax.bar(down.index, down['High'] - down['Open'], bottom=down['Open'], 
                   color='blue', alpha=0.7, width=0.1)
            ax.bar(down.index, down['Low'] - down['Close'], bottom=down['Close'], 
                   color='blue', alpha=0.7, width=0.1)
        
        ax.set_title(f'{ticker} - {company_name} Stock Price Chart', fontsize=16, fontweight='bold')
        ax.set_ylabel('Price (JPY)', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # x軸の日付フォーマット
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    def plot_moving_averages(self, ax, data):
        """移動平均線を描画"""
        colors = ['blue', 'orange', 'purple', 'brown']
        periods = ['MA5', 'MA25', 'MA75', 'MA200']
        labels = ['5-day MA', '25-day MA', '75-day MA', '200-day MA']
        
        for color, period, label in zip(colors, periods, labels):
            if period in data.columns and not data[period].isna().all():
                ax.plot(data.index, data[period], color=color, linewidth=0.8, 
                       label=label, alpha=0.8)
        
        ax.legend(loc='upper left', fontsize=10)
    
    def plot_volume(self, ax, data):
        """出来高を描画"""
        # 上昇・下降の判定
        up = data[data['Close'] >= data['Open']]
        down = data[data['Close'] < data['Open']]
        
        # 上昇日の出来高（赤）
        if not up.empty:
            ax.bar(up.index, up['Volume'], color='red', alpha=0.7, width=0.8)
        
        # 下降日の出来高（青）
        if not down.empty:
            ax.bar(down.index, down['Volume'], color='blue', alpha=0.7, width=0.8)
        
        ax.set_ylabel('Volume', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # x軸の日付フォーマット
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    def run(self):
        """メイン実行関数"""
        try:
            # ユーザー入力取得
            ticker, period = self.get_user_input()
            
            # データ取得
            data, company_name = self.fetch_stock_data(ticker, period)
            if data is None:
                return False
            
            # チャート作成
            filepath = self.create_chart(data, ticker, period, company_name)
            
            print(f"\n=== Completed ===")
            print(f"Ticker: {ticker}")
            print(f"Company: {company_name}")
            print(f"Period: {self.periods[period]}")
            print(f"Saved to: {filepath}")
            
            return True
            
        except KeyboardInterrupt:
            print("\n\nProcess interrupted.")
            return False
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            return False

def main():
    """メイン関数"""
    generator = ChartGenerator()
    success = generator.run()
    
    if success:
        print("\nChart generation completed successfully.")
    else:
        print("\nChart generation failed.")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
