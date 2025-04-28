# main.py の修正版
import os
import sys
import logging
import pandas as pd
from datetime import datetime
import argparse

# モジュール参照のためにパスを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)  # カレントディレクトリをパスに追加

# 自作モジュールのインポート
import config
from data_loader import load_industry_list, get_industry_volume_data
from volume_analyzer import calculate_moving_averages, save_analysis_results

def parse_arguments():
    """
    コマンドライン引数を解析
    """
    parser = argparse.ArgumentParser(description='出来高移動平均分析プログラム')
    parser.add_argument('--test', action='store_true', help='テストモードで実行')
    return parser.parse_args()

def main():
    """
    メイン処理
    """
    # 開始メッセージ
    mode_str = "テストモード" if config.TEST_MODE else "通常モード"
    logging.info(f"出来高移動平均分析を開始します [{mode_str}]")
    start_time = datetime.now()
    
    try:
        # 業種リストを読み込む
        logging.info(f"業種リストを読み込みます: {config.INPUT_FILE_PATH}")
        industry_df = load_industry_list(config.INPUT_FILE_PATH)
        
        # 業種ごとの出来高データを取得
        logging.info(f"業種ごとの出来高データを取得します (期間: {config.STOCK_HISTORY_PERIOD})")
        volume_data = get_industry_volume_data(industry_df, config.STOCK_HISTORY_PERIOD)
        
        # 出来高の移動平均を計算
        logging.info(f"移動平均を計算します (短期: {config.SHORT_TERM_PERIOD}日, 長期: {config.LONG_TERM_PERIOD}日)")
        analysis_results = calculate_moving_averages(volume_data, config.SHORT_TERM_PERIOD, config.LONG_TERM_PERIOD)
        
        # 結果を保存
        logging.info(f"分析結果を保存します: {config.OUTPUT_DIR}")
        output_files = save_analysis_results(
            analysis_results, 
            config.OUTPUT_DIR, 
            config.ALL_INDUSTRIES_FILE, 
            config.ABOVE_MA_FILE, 
            config.BELOW_MA_FILE
        )
        
        # 実行結果の要約を表示
        print("\n===== 分析結果の要約 =====")
        print(f"処理した業種数: {len(analysis_results)}")
        print(f"短期MAが長期MAを上回る業種数: {len(analysis_results[analysis_results['Status'] == '上回る'])}")
        print(f"短期MAが長期MAを下回る業種数: {len(analysis_results[analysis_results['Status'] == '下回る'])}")
        print(f"\n出力ファイル:")
        for file_type, file_path in output_files.items():
            print(f"- {file_type}: {file_path}")
        
        # 実行時間を表示
        end_time = datetime.now()
        execution_time = end_time - start_time
        print(f"\n実行時間: {execution_time}")
        
    except Exception as e:
        logging.error(f"処理中にエラーが発生しました: {e}")
        raise
    
    logging.info("出来高移動平均分析を終了します")

if __name__ == "__main__":
    # コマンドライン引数の解析
    args = parse_arguments()
    
    # テストモード設定をconfigに反映
    if args.test:
        config.TEST_MODE = True
        # テストモード時のファイル名を更新
        config.ALL_INDUSTRIES_FILE = "test_" + config.ALL_INDUSTRIES_FILE
        config.ABOVE_MA_FILE = "test_" + config.ABOVE_MA_FILE
        config.BELOW_MA_FILE = "test_" + config.BELOW_MA_FILE
    
    # 出力ディレクトリが存在しない場合は作成
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    
    # ロギング設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join(config.OUTPUT_DIR, 'volume_analysis.log'), 'w', 'utf-8')
        ]
    )
    
    # メイン処理を実行
    main()