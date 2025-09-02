"""
メインスクリプト - 株価データ取得・分析・シグナル抽出の統合実行エントリーポイント

このスクリプトは株価データの取得、テクニカル指標の計算、売買シグナルの抽出、
レンジブレイク銘柄の検出、強気/弱気トレンド銘柄の抽出、押し目銘柄の検出、
BB-MACDシグナル抽出、一目均衡表シグナル抽出までの一連の処理を統合的に実行します。

WordPress投稿とチャート生成は別スクリプト（Upload_WardPress.py）で実行されます。
"""
import os
import sys
import argparse
import logging
import importlib
from typing import List
from datetime import datetime

# モジュールのパスをPythonパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 自作モジュールのインポート
import config  # 設定値を管理するモジュール
from data_loader import setup_logger, load_company_list  # ロガー設定と企業リスト読み込み関数
from stock_fetcher import fetch_stock_data  # 株価データを取得する関数
from technical_indicators import calculate_signals  # テクニカル指標を計算する関数
from technical_indicators import extract_BB_MACD_signals, get_BB_MACD_signal_summary
from extract_signals import extract_signals, extract_strong_buying_trend, extract_strong_selling_trend, extract_all_ichimoku_signals, extract_push_mark_signals  # 売買シグナルとトレンド銘柄を抽出する関数
from breakout import identify_breakouts  # ブレイク銘柄抽出関数
from result_backup import backup_previous_results  # 前回結果のバックアップ機能

def main():
    """
    メイン処理 - 株価データ取得からシグナル抽出までの一連の処理を実行
    
    処理の流れ：
    1. コマンドライン引数の解析（テストモード判定）
    2. ロガーの設定
    3. 企業リストの読み込み
    4. 株価データの取得（yfinance API使用）
    5. テクニカル指標の計算（移動平均、RSI、MACD、RCI、一目均衡表など）
    6. 売買シグナルの抽出（MACD-RSI、MACD-RCI、BB-MACD）
    7. レンジブレイク銘柄の検出
    8. 強気/弱気トレンド銘柄の抽出
    9. 押し目銘柄の検出
    10. 一目均衡表シグナルの抽出
    
    Returns:
        int: 成功時は0、エラー時は1
    """
    # コマンドライン引数の解析 - テストモードのフラグを受け取る
    parser = argparse.ArgumentParser(description='株価データ取得・分析・シグナル抽出ツール')
    parser.add_argument('--test', action='store_true', help='テストモードで実行（少数銘柄で動作確認）')

    args = parser.parse_args()
    
    # テストモードかどうかのフラグを保存
    is_test_mode = args.test
    
    # ロガーの設定（テストモードに応じた設定）
    # テストモードではより詳細なログレベルや別のログファイルを使用する可能性がある
    logger = setup_logger(is_test_mode)
    logger.info("=== 株価データ取得・分析・シグナル抽出ツール 開始 ===")
    logger.info(f"実行モード: {'テスト' if is_test_mode else '通常'}")
    
    # 前回の結果ファイルをバックアップ（新しい結果生成前に実行）
    logger.info("前回の結果ファイルをバックアップしています...")
    backup_previous_results()
    logger.info("前回の結果ファイルのバックアップが完了しました。")
    
    try:
        # 企業リストの読み込み
        # テストモードの場合は限定された企業リストを読み込む
        tickers = load_company_list(is_test_mode)
        
        # 企業リストが空の場合はエラーを記録して処理を終了
        if not tickers:
            logger.error("企業リストが空です。処理を終了します。")
            return 1
        
        # 株価データの取得
        # configモジュールから設定値（バッチサイズ、期間など）を取得して実行
        stock_data = fetch_stock_data(tickers, is_test_mode=is_test_mode)
        
        # テクニカル指標の計算処理を開始
        logger.info("テクニカル指標の計算を開始します...")
        
        try:
            # 各銘柄に対してテクニカル指標（移動平均、RSI、MACD、RCI、一目均衡表など）を計算
            signal_results = calculate_signals(tickers, is_test_mode)
            logger.info("テクニカル指標の計算が完了しました。")
            
            # 計算されたテクニカル指標に基づいて売買シグナルを抽出
            logger.info("Buy/Sellシグナルの抽出を開始します...")
            extract_success = extract_signals(is_test_mode)
            
            # シグナル抽出後にブレイク銘柄の抽出処理を実行
            logger.info("ブレイク銘柄の抽出を開始します...")
            breakout_success = identify_breakouts(is_test_mode)
                        
            # ブレイク抽出の結果をログに記録
            if breakout_success:
                logger.info("ブレイク銘柄の抽出が完了しました。")
            else:
                logger.error("ブレイク銘柄の抽出中にエラーが発生しました。")
            
            # シグナル抽出の結果をログに記録
            if extract_success:
                logger.info("Buy/Sellシグナルの抽出が完了しました。")
            else:
                logger.error("Buy/Sellシグナルの抽出中にエラーが発生しました。")
            
            # シグナル抽出後に強気トレンド銘柄の抽出処理を実行
            logger.info("強気トレンド銘柄の抽出を開始します...")
            strong_buying_success = extract_strong_buying_trend(is_test_mode)
                        
            # 強気トレンド抽出の結果をログに記録
            if strong_buying_success:
                logger.info("強気トレンド銘柄の抽出が完了しました。")
            else:
                logger.error("強気トレンド銘柄の抽出中にエラーが発生しました。")

            # 強気トレンド銘柄抽出後に、強気売りトレンド銘柄の抽出処理を実行
            logger.info("強気売りトレンド銘柄の抽出を開始します...")
            strong_selling_success = extract_strong_selling_trend(is_test_mode)
                        
            # 強気売りトレンド抽出の結果をログに記録
            if strong_selling_success:
                logger.info("強気売りトレンド銘柄の抽出が完了しました。")
            else:
                logger.error("強気売りトレンド銘柄の抽出中にエラーが発生しました。")
            
            # 押し目銘柄の抽出処理を実行
            logger.info("押し目銘柄の抽出を開始します...")
            push_mark_success = extract_push_mark_signals(is_test_mode)
                                
            # 押し目銘柄抽出の結果をログに記録
            if push_mark_success:
                logger.info("押し目銘柄の抽出が完了しました。")
            else:
                logger.error("押し目銘柄の抽出中にエラーが発生しました。")
            
            # BB-MACDシグナル抽出処理を実行（extract_signals.pyと同じ場所に出力）
            logger.info("BB-MACDシグナル銘柄の抽出を開始します...")
            bb_macd_results = extract_BB_MACD_signals(is_test_mode)

            # BB-MACDシグナル抽出の結果をログに記録
            if bb_macd_results:
                logger.info("BB-MACDシグナル銘柄の抽出が完了しました。")
                
                # サマリー統計の取得と表示
                # summary = get_BB_MACD_signal_summary(is_test_mode)
            else:
                logger.error("BB-MACDシグナル銘柄の抽出中にエラーが発生しました。")
                
            # 一目均衡表のシグナル抽出処理を実行
            logger.info("一目均衡表情報の抽出を開始します...")
            ichimoku_results = extract_all_ichimoku_signals(is_test_mode)

            # 一目均衡表のシグナル抽出の結果をログに記録
            if ichimoku_results:
                logger.info("一目均衡表情報の抽出が完了しました。")
            
            else:
                logger.error("一目均衡表情報の抽出中にエラーが発生しました。")
    
        except Exception as e:
            # テクニカル指標計算中のエラーハンドリング
            logger.error(f"テクニカル指標の計算中にエラーが発生しました: {str(e)}")
    
        # チャート生成はUpload_WardPress.pyで実行されます
        logger.info("チャート生成はUpload_WardPress.pyで実行されます")
        
        # 全処理の完了を記録して正常終了
        logger.info("=== 株価データ取得・分析・シグナル抽出ツール 終了 ===")
        return 0
        
    except Exception as e:
        # メイン処理全体での例外をキャッチしてログに記録
        logger.error(f"予期せぬエラーが発生しました: {str(e)}")
        return 1

# スクリプトが直接実行された場合のみmain関数を実行
# 戻り値をsys.exitに渡してプロセスの終了コードを設定
if __name__ == "__main__":
    sys.exit(main())