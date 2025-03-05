"""
株価取得モジュール - yfinanceを使用して株価データを取得します
"""
import os
import time
import pandas as pd
import yfinance as yf
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

def fetch_stock_data(tickers: List[str], batch_size: int = 10, is_test_mode: bool = False) -> Dict[str, Optional[pd.DataFrame]]:
    """
    指定された銘柄コードリストに対して、バッチ処理で株価データを取得します
    
    Args:
        tickers: 銘柄コードのリスト
        batch_size: 一度に処理する銘柄の数
        is_test_mode: テストモードかどうか
        
    Returns:
        Dict[str, Optional[pd.DataFrame]]: 銘柄コードをキー、株価データを値とする辞書
    """
    import config
    
    logger = logging.getLogger("StockSignal")
    stock_data = {}
    
    # 保存用ディレクトリの設定
    data_dir = config.TEST_RESULT_DIR if is_test_mode else config.RESULT_DIR
    os.makedirs(data_dir, exist_ok=True)
    
    logger.info(f"株価データの取得を開始します。対象企業数: {len(tickers)}")
    logger.info(f"取得期間: {config.HISTORY_PERIOD}")
    
    # バッチ処理
    for i in range(0, len(tickers), batch_size):
        batch_tickers = tickers[i:i+batch_size]
        logger.info(f"バッチ処理: {i+1}～{min(i+batch_size, len(tickers))}社 ({len(tickers)}社中)")
        
        for ticker in batch_tickers:
            try:
                # 日本の銘柄コードに.Tを付加
                yf_ticker = f"{ticker}{config.YF_SUFFIX}" if not ticker.endswith(config.YF_SUFFIX) else ticker
                logger.info(f"銘柄 {ticker} の株価データを取得中...")
                
                # yfinanceでデータ取得
                stock = yf.Ticker(yf_ticker)
                hist = stock.history(period=config.HISTORY_PERIOD)
                
                if hist.empty:
                    logger.warning(f"銘柄 {ticker} のデータが取得できませんでした")
                    stock_data[ticker] = None
                    continue
                
                # データを保存
                csv_path = os.path.join(data_dir, f"{ticker}.csv")
                hist.to_csv(csv_path)
                logger.info(f"銘柄 {ticker} のデータを保存しました")
                
                stock_data[ticker] = hist
                
            except Exception as e:
                logger.error(f"銘柄 {ticker} のデータ取得中にエラーが発生しました: {str(e)}")
                stock_data[ticker] = None
        
        # API制限を避けるために少し待機
        if i + batch_size < len(tickers):
            logger.info("API制限を避けるために2秒間待機します...")
            time.sleep(2)
    
    logger.info(f"株価データの取得が完了しました。成功: {sum(1 for v in stock_data.values() if v is not None)}社, 失敗: {sum(1 for v in stock_data.values() if v is None)}社")
    
    return stock_data