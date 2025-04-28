# data_loader.py 修正版
import pandas as pd
import yfinance as yf
import os
import time
from datetime import datetime, timedelta
import logging
import config

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_industry_list(file_path):
    """
    業種リストを読み込む
    """
    try:
        df = pd.read_csv(file_path)
        
        # カラム名を確認するログを追加
        logging.info(f"CSVファイルのカラム名: {list(df.columns)}")
        
        # 業種と銘柄コードの列名を確認
        if '33業種区分' not in df.columns:
            logging.error("CSVファイルに '33業種区分' 列が見つかりません")
            raise ValueError("業種列が見つかりません。CSVファイルの形式を確認してください。")
        
        # カラム名をマッピング
        df = df.rename(columns={'33業種区分': 'Industry'})
        
        # Ticker列の確認と名前変更（必要に応じて）
        ticker_column = None
        for col in df.columns:
            if col.lower() in ['ticker', 'code', '銘柄コード', 'stock_code']:
                ticker_column = col
                break
        
        if ticker_column is None:
            logging.error(f"銘柄コード列が見つかりませんでした。カラム一覧: {list(df.columns)}")
            raise ValueError("銘柄コード列が見つかりません。CSVファイルの形式を確認してください。")
        else:
            logging.info(f"銘柄コード列として '{ticker_column}' を使用します")
            if ticker_column != 'Ticker':
                df = df.rename(columns={ticker_column: 'Ticker'})
        
        # テストモードの場合、一部の銘柄のみ使用
        if config.TEST_MODE:
            # 業種ごとに均等に銘柄を選択するため、グループ化して抽出
            industries = df['Industry'].unique()
            selected_df = pd.DataFrame()
            
            for industry in industries:
                industry_df = df[df['Industry'] == industry]
                # 各業種から最大TEST_TICKERS_COUNT/len(industries)銘柄を選択
                sample_size = max(1, min(len(industry_df), int(config.TEST_TICKERS_COUNT / len(industries))))
                industry_sample = industry_df.sample(n=sample_size)
                selected_df = pd.concat([selected_df, industry_sample])
            
            df = selected_df
            logging.info(f"テストモード: {len(df)}銘柄を選択しました")
        
        logging.info(f"業種リストを読み込みました。合計: {len(df)} 銘柄")
        return df
    except Exception as e:
        logging.error(f"業種リストの読み込みに失敗しました: {e}")
        raise

def get_stock_data(ticker, period):
    """
    指定された銘柄の株価データを取得する
    """
    try:
        # 日本株の場合、ティッカーに'.T'を追加
        if not ticker.endswith('.T'):
            ticker = f"{ticker}.T"
        
        # yfinanceからデータ取得
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        
        # データがあるか確認
        if hist.empty:
            logging.warning(f"{ticker}のデータが空です")
            return None
        
        return hist
    except Exception as e:
        logging.warning(f"{ticker}のデータ取得に失敗しました: {e}")
        return None
        
def get_industry_volume_data(industry_df, period):
    """
    業種ごとの出来高データを集計する
    """
    # 業種ごとのデータを格納する辞書
    industry_volume_data = {}
    total_tickers = len(industry_df)
    
    # 進捗状況を表示するためのカウンター
    counter = 0
    
    # 各ティッカーごとに処理
    for idx, row in industry_df.iterrows():
        ticker = row['Ticker']
        industry = row['Industry']
        
        counter += 1
        if counter % 10 == 0:
            logging.info(f"処理中... {counter}/{total_tickers} ({(counter/total_tickers*100):.1f}%)")
        
        # 株価データ取得
        hist = get_stock_data(ticker, period)
        
        if hist is None or len(hist) < config.LONG_TERM_PERIOD:  # 長期移動平均の期間より短いデータは除外
            continue
        
        # 出来高データを抽出
        volume_data = hist['Volume'].copy()
        
        # 業種ごとにデータを集計
        if industry not in industry_volume_data:
            industry_volume_data[industry] = volume_data
        else:
            # 業種内の銘柄の出来高を合計
            industry_volume_data[industry] = industry_volume_data[industry].add(volume_data, fill_value=0)
            
        # APIの制限を考慮して少し待機
        time.sleep(0.1)
    
    # 辞書からDataFrameを作成
    result_df = pd.DataFrame({industry: data for industry, data in industry_volume_data.items()})
    
    return result_df