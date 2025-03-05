"""
データローダーモジュール - CSVファイルから企業リストを読み込みます
"""
import os
import pandas as pd
import logging
from typing import List, Optional

def setup_logger(is_test_mode=False):
    """ロガーの設定"""
    import config
    
    # テストモードに応じてログディレクトリを設定
    log_dir = config.TEST_LOG_DIR if is_test_mode else config.LOG_DIR
    
    # ログディレクトリがない場合は作成
    os.makedirs(log_dir, exist_ok=True)
    
    # ログファイルパスの設定
    log_file = os.path.join(log_dir, config.LOG_FILE_NAME)
    
    # ロガーの設定
    logger = logging.getLogger("StockSignal")
    logger.setLevel(logging.INFO)
    
    # 既存のハンドラをクリア
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # ファイルハンドラ
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # コンソールハンドラ
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # フォーマッタ
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # ハンドラの追加
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def load_company_list(is_test_mode: bool = False) -> List[str]:
    """
    企業リストを読み込み、銘柄コードのリストを返します
    
    Args:
        is_test_mode: テストモードかどうか
        
    Returns:
        List[str]: 銘柄コードのリスト
    """
    import config
    
    logger = logging.getLogger("StockSignal")
    
    try:
        if is_test_mode:
            file_path = os.path.join(config.TEST_DIR, config.COMPANY_LIST_TEST_FILE)
            logger.info(f"テストモード: {file_path} からデータを読み込みます")
        else:
            file_path = os.path.join(config.BASE_DIR, config.COMPANY_LIST_FILE)
            logger.info(f"通常モード: {file_path} からデータを読み込みます")
        
        if not os.path.exists(file_path):
            logger.error(f"ファイルが見つかりません: {file_path}")
            return []
        
        df = pd.read_csv(file_path, encoding='utf-8')
        
        # 'Ticker'列の存在チェック
        if 'Ticker' not in df.columns:
            logger.error(f"'Ticker'列がCSVファイルに見つかりません: {file_path}")
            return []
        
        # 銘柄コードのリストを取得
        tickers = df['Ticker'].tolist()
        logger.info(f"{len(tickers)}社の銘柄コードを読み込みました")
        
        return tickers
        
    except Exception as e:
        logger.error(f"企業リストの読み込み中にエラーが発生しました: {str(e)}")
        return []