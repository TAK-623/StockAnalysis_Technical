"""
ブレイク銘柄のROE情報をyfinanceから取得してBreakout.csvに追加するスクリプト

このスクリプトは以下の処理を行います：
1. Breakout.csvを読み込み
2. 各銘柄のROE情報をyfinanceから取得
3. ROE情報を終値の右の列に追加
4. 更新されたCSVファイルを保存
"""

import os
import pandas as pd
import yfinance as yf
import logging
import time
from typing import Optional
import config

def setup_logger() -> logging.Logger:
    """ロガーの設定"""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def get_roe_for_ticker(ticker: str, logger: logging.Logger) -> Optional[float]:
    """
    指定された銘柄のROE情報をyfinanceから取得
    
    Args:
        ticker: 銘柄コード（例: "7203.T"）
        logger: ロガーオブジェクト
    
    Returns:
        ROE値（パーセンテージ）、取得できない場合はNone
    """
    try:
        # 日本株の場合は.Tを付ける
        if not ticker.endswith('.T'):
            ticker_with_suffix = f"{ticker}.T"
        else:
            ticker_with_suffix = ticker
        
        # yfinanceでティッカー情報を取得
        stock = yf.Ticker(ticker_with_suffix)
        
        # 基本情報からROEを直接取得
        info = stock.info
        roe = info.get('returnOnEquity')
        
        if roe is not None:
            # 小数形式をパーセンテージに変換
            roe_percentage = roe * 100
            return round(roe_percentage, 2)
        else:
            logger.warning(f"{ticker}: ROE情報が取得できませんでした")
            return None
            
    except Exception as e:
        logger.error(f"{ticker}: ROE取得中にエラーが発生しました: {str(e)}")
        return None

def add_roe_to_breakout_csv(is_test_mode: bool = False) -> bool:
    """
    Breakout.csvにROE情報を追加するメイン関数
    
    Args:
        is_test_mode: テストモードかどうか
    
    Returns:
        処理が成功したかどうか
    """
    logger = setup_logger()
    logger.info("ROE情報の追加処理を開始します...")
    
    try:
        # ファイルパスの設定
        if is_test_mode:
            breakout_file = os.path.join(config.TEST_DIR, "Result", "Breakout.csv")
        else:
            breakout_file = os.path.join(config.BASE_DIR, "StockSignal", "Result", "Breakout.csv")
        
        # Breakout.csvが存在するかチェック
        if not os.path.exists(breakout_file):
            logger.error(f"Breakout.csvが見つかりません: {breakout_file}")
            return False
        
        # CSVファイルを読み込み
        df = pd.read_csv(breakout_file, encoding='utf-8-sig')
        logger.info(f"Breakout.csvを読み込みました。銘柄数: {len(df)}")
        
        # ROE列を追加（初期値はNaN）
        df['ROE(%)'] = None
        
        # 各銘柄のROE情報を取得
        for index, row in df.iterrows():
            ticker = str(row['Ticker'])
            company = row['Company']
            
            logger.info(f"処理中 ({index + 1}/{len(df)}): {ticker} - {company}")
            
            # ROE情報を取得
            roe = get_roe_for_ticker(ticker, logger)
            
            if roe is not None:
                df.at[index, 'ROE(%)'] = roe
                logger.info(f"  ROE: {roe}%")
            else:
                logger.warning(f"  ROE取得失敗")
            
            # API制限を避けるため少し待機
            time.sleep(0.5)
        
        # 列の順序を調整（ROEを終値の右隣に配置）
        columns = list(df.columns)
        close_index = columns.index('終値')
        
        # ROE列を終値の右隣に移動
        if 'ROE(%)' in columns:
            columns.remove('ROE(%)')
            columns.insert(close_index + 1, 'ROE(%)')
            df = df[columns]
        
        # 更新されたCSVファイルを保存
        df.to_csv(breakout_file, index=False, encoding='utf-8-sig')
        
        # ROE取得成功数をカウント
        roe_success_count = df['ROE(%)'].notna().sum()
        logger.info(f"ROE情報の追加が完了しました。")
        logger.info(f"成功: {roe_success_count}/{len(df)} 銘柄")
        logger.info(f"ファイル保存先: {breakout_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"ROE情報の追加処理中にエラーが発生しました: {str(e)}")
        return False

def main():
    """メイン関数"""
    logger = setup_logger()
    
    # 通常モードで実行
    success = add_roe_to_breakout_csv(is_test_mode=False)
    
    if success:
        logger.info("処理が正常に完了しました。")
    else:
        logger.error("処理が失敗しました。")

if __name__ == "__main__":
    main()
