"""
メインスクリプト - データ取得処理を実行します
"""
import os
import sys
import argparse
import logging
import importlib
from typing import List

# モジュールのパスをPythonパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 自作モジュールのインポート
import config
from data_loader import setup_logger, load_company_list
from stock_fetcher import fetch_stock_data
from technical_indicators import calculate_signals
from extract_signals import extract_signals

def main():
    """メイン処理"""
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='株価データ取得ツール')
    parser.add_argument('--test', action='store_true', help='テストモードで実行')
    args = parser.parse_args()
    
    # テストモードかどうか
    is_test_mode = args.test
    
    # ロガーの設定（テストモードに応じた設定）
    logger = setup_logger(is_test_mode)
    logger.info("=== 株価データ取得ツール 開始 ===")
    logger.info(f"実行モード: {'テスト' if is_test_mode else '通常'}")
    
    try:
        # 企業リストの読み込み
        tickers = load_company_list(is_test_mode)
        
        if not tickers:
            logger.error("企業リストが空です。処理を終了します。")
            return 1
        
        # 株価データの取得（バッチサイズなどの設定はすべてconfigから取得）
        stock_data = fetch_stock_data(tickers, is_test_mode=is_test_mode)
        
        # テクニカル指標の計算
        logger.info("テクニカル指標の計算を開始します...")
        
        try:
            signal_results = calculate_signals(tickers, is_test_mode)
            logger.info("テクニカル指標の計算が完了しました。")
            
            # シグナル抽出処理の追加
            logger.info("Buy/Sellシグナルの抽出を開始します...")
            extract_success = extract_signals(is_test_mode)
            if extract_success:
                logger.info("Buy/Sellシグナルの抽出が完了しました。")
            else:
                logger.error("Buy/Sellシグナルの抽出中にエラーが発生しました。")
            
        except Exception as e:
            logger.error(f"テクニカル指標の計算中にエラーが発生しました: {str(e)}")
        
        logger.info("=== 株価データ取得ツール 終了 ===")
        return 0
        
    except Exception as e:
        logger.error(f"予期せぬエラーが発生しました: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())