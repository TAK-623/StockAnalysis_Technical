"""
シグナル抽出モジュール - latest_signal.csvから買い/売りシグナルを抽出してCSVファイルに出力します
"""
import os
import pandas as pd
import logging
from typing import Optional

def extract_signals(is_test_mode: bool = False) -> bool:
    """
    latest_signal.csvからBuy/Sellシグナルを抽出してCSVファイルに出力します
    
    Args:
        is_test_mode: テストモードかどうか
        
    Returns:
        bool: 処理が成功したかどうか
    """
    import config
    
    logger = logging.getLogger("StockSignal")
    logger.info("Buy/Sellシグナルの抽出を開始します")
    
    try:
        # 入力ファイルのパスを設定
        if is_test_mode:
            input_dir = os.path.join(config.TEST_DIR, "TechnicalSignal")
        else:
            input_dir = os.path.join(config.BASE_DIR, "TechnicalSignal")
        
        input_file = os.path.join(input_dir, config.LATEST_SIGNAL_FILE)
        
        # 出力ディレクトリの設定
        if is_test_mode:
            output_dir = os.path.join(config.TEST_DIR, "Result")
        else:
            output_dir = os.path.join(config.BASE_DIR, "Result")
        
        # 出力ディレクトリの作成
        os.makedirs(output_dir, exist_ok=True)
        
        # 入力ファイルの存在確認
        if not os.path.exists(input_file):
            logger.error(f"ファイルが見つかりません: {input_file}")
            return False
        
        # CSVの読み込み
        logger.info(f"{input_file} を読み込みます")
        df = pd.read_csv(input_file, index_col=0, parse_dates=True)
        
        # 日付カラムがある場合はそれも日付型に変換
        date_columns = [col for col in df.columns if col.lower() in ['date', 'datetime', '日付']]
        for col in date_columns:
            df[col] = pd.to_datetime(df[col])
        
        # 必要なカラムの存在確認
        required_columns = ['Ticker', 'Company', 'Signal']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"必要なカラムがCSVファイルに見つかりません: {missing_columns}")
            return False
        
        # Buyシグナルの抽出
        buy_signals = df[df['Signal'] == 'Buy'][['Ticker', 'Company', 'Signal']]
        buy_output_file = os.path.join(output_dir, "signal_result_buy.csv")
        
        # Sellシグナルの抽出
        sell_signals = df[df['Signal'] == 'Sell'][['Ticker', 'Company', 'Signal']]
        sell_output_file = os.path.join(output_dir, "signal_result_sell.csv")
        
        # 日付列の追加と形式変換
        # 日付形式を変換するためのフォーマット関数
        def add_formatted_date(df):
            df_with_date = df.copy()
            
            # インデックスが日付型の場合
            if isinstance(df.index, pd.DatetimeIndex):
                df_with_date['Date'] = df.index.strftime('%Y/%m/%d')
            else:
                # インデックスが日付型でない場合は変換を試みる
                try:
                    dates = pd.to_datetime(df.index)
                    df_with_date['Date'] = dates.strftime('%Y/%m/%d')
                except:
                    # 変換できない場合は現在の日付を使用
                    import datetime
                    current_date = datetime.datetime.now().strftime('%Y/%m/%d')
                    df_with_date['Date'] = current_date
            
            # Dateカラムを先頭に移動
            cols = df_with_date.columns.tolist()
            cols.insert(0, cols.pop(cols.index('Date')))
            df_with_date = df_with_date[cols]
            
            return df_with_date
        
        # 日付列を追加してフォーマット
        buy_signals_formatted = add_formatted_date(buy_signals)
        sell_signals_formatted = add_formatted_date(sell_signals)
        
        # 結果をCSVファイルに出力 (インデックスは出力しない)
        buy_signals_formatted.to_csv(buy_output_file, index=False)
        sell_signals_formatted.to_csv(sell_output_file, index=False)
        
        logger.info(f"Buyシグナル: {len(buy_signals)}件を {buy_output_file} に出力しました")
        logger.info(f"Sellシグナル: {len(sell_signals)}件を {sell_output_file} に出力しました")
        
        return True
        
    except Exception as e:
        logger.error(f"シグナル抽出処理中にエラーが発生しました: {str(e)}")
        return False

# モジュールとして使用される場合は以下は実行されません
if __name__ == "__main__":
    import sys
    import argparse
    
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='Buy/Sellシグナル抽出ツール')
    parser.add_argument('--test', action='store_true', help='テストモードで実行')
    args = parser.parse_args()
    
    # ロガーの設定
    from data_loader import setup_logger
    logger = setup_logger(args.test)
    
    # シグナル抽出実行
    success = extract_signals(args.test)
    
    # 終了コードの設定
    sys.exit(0 if success else 1)