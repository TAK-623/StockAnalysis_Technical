"""
シグナル抽出モジュール - latest_signal.csvから買い/売りシグナルを抽出してCSVファイルに出力します
このモジュールは、テクニカル分析によって生成されたシグナル情報から、
特に注目すべき「買い」と「売り」シグナルを抽出し、個別のCSVファイルとして
整理・出力する機能を提供します。単独実行も、他のモジュールからの呼び出しも可能です。
"""
import os
import pandas as pd
import logging
from typing import Optional

def extract_signals(is_test_mode: bool = False) -> bool:
    """
    latest_signal.csvからBuy/Sellシグナルを抽出してCSVファイルに出力します
    
    このテクニカル指標分析結果ファイルから、「Buy（買い）」と「Sell（売り）」のシグナルが
    出ている銘柄をそれぞれ抽出し、個別のCSVファイルとして保存します。
    テストモードでは、テスト用ディレクトリのデータを使用します。
    
    Args:
        is_test_mode (bool): テストモードの場合はTrue、通常モードの場合はFalse
        
    Returns:
        bool: 処理が成功した場合はTrue、エラーが発生した場合はFalse
    """
    import config  # 設定値モジュールをインポート
    
    # StockSignal名前付きロガーを取得
    logger = logging.getLogger("StockSignal")
    logger.info("Buy/Sellシグナルの抽出を開始します")
    
    try:
        # 入力ファイルのパスを設定
        # テストモードと通常モードで異なるディレクトリを使用
        if is_test_mode:
            # テストモード: テスト用ディレクトリ内のTechnicalSignalフォルダを使用
            input_dir = os.path.join(config.TEST_DIR, "TechnicalSignal")
        else:
            # 通常モード: 本番用ディレクトリ内のTechnicalSignalフォルダを使用
            input_dir = os.path.join(config.BASE_DIR, "TechnicalSignal")
        
        # 入力ファイルのフルパスを生成 (latest_signal.csv)
        input_file = os.path.join(input_dir, config.LATEST_SIGNAL_FILE)
        
        # 出力ディレクトリの設定
        # テストモードと通常モードで異なる出力先を使用
        if is_test_mode:
            # テストモード: テスト用ディレクトリ内のResultフォルダに出力
            output_dir = os.path.join(config.TEST_DIR, "Result")
        else:
            # 通常モード: 本番用ディレクトリ内のResultフォルダに出力
            output_dir = os.path.join(config.BASE_DIR, "Result")
        
        # 出力ディレクトリが存在しない場合は作成
        # exist_ok=Trueにより、ディレクトリが既に存在してもエラーにならない
        os.makedirs(output_dir, exist_ok=True)
        
        # 入力ファイルの存在確認
        # ファイルが存在しない場合はエラーログを出力して処理を中断
        if not os.path.exists(input_file):
            logger.error(f"ファイルが見つかりません: {input_file}")
            return False
        
        # CSVの読み込み
        # index_col=0: 最初の列をインデックスとして扱う
        # parse_dates=True: 日付列を日付型として解析
        logger.info(f"{input_file} を読み込みます")
        df = pd.read_csv(input_file, index_col=0, parse_dates=True)
        
        # RSI長期の列名を取得（config.RSI_LONG_PERIODの値に基づく）
        rsi_long_col = f'RSI{config.RSI_LONG_PERIOD}'
        
        # 必要なカラムの存在確認
        # データフレームに必要なカラムが含まれているか検証
        required_columns = ['Ticker', 'Company', 'Signal', 'Close', 'MACD', rsi_long_col]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            # 必要なカラムが見つからない場合はエラーログを出力して処理を中断
            logger.error(f"必要なカラムがCSVファイルに見つかりません: {missing_columns}")
            return False
        
        # Buyシグナルの抽出処理
        # 1. Signalカラムが'Buy'のレコードのみを抽出
        # 2. 必要なカラム（銘柄コード、会社名、終値、MACD、RSI長期）のみを選択
        buy_signals = df[df['Signal'] == 'Buy'][['Ticker', 'Company', 'Close', 'MACD', rsi_long_col]]
        
        # 数値データの小数点以下桁数を調整（小数点以下2桁に丸める）
        buy_signals['MACD'] = buy_signals['MACD'].round(2)
        buy_signals[rsi_long_col] = buy_signals[rsi_long_col].round(2)
        
        # カラム名を日本語に変更（レポートの可読性向上のため）
        buy_signals = buy_signals.rename(columns={
            'Close': '終値',
            'MACD': 'MACD',
            rsi_long_col: f'RSI{config.RSI_LONG_PERIOD}'
        })
        # 買いシグナル出力ファイルのパスを設定
        buy_output_file = os.path.join(output_dir, "signal_result_buy.csv")
        
        # Sellシグナルの抽出処理
        # 1. Signalカラムが'Sell'のレコードのみを抽出
        # 2. 必要なカラム（銘柄コード、会社名、終値、MACD、RSI長期）のみを選択
        sell_signals = df[df['Signal'] == 'Sell'][['Ticker', 'Company', 'Close', 'MACD', rsi_long_col]]
        
        # 数値データの小数点以下桁数を調整
        sell_signals['MACD'] = sell_signals['MACD'].round(2)
        sell_signals[rsi_long_col] = sell_signals[rsi_long_col].round(2)
        
        # 終値の表示形式を調整（小数点以下が0の場合は整数表示、それ以外は小数点以下1桁）
        sell_signals['Close'] = sell_signals['Close'].apply(
            lambda x: int(x) if x == int(x) else round(x, 1)
        )
        
        # カラム名を日本語に変更（レポートの可読性向上のため）
        sell_signals = sell_signals.rename(columns={
            'Close': '終値',
            'MACD': 'MACD',
            rsi_long_col: f'RSI{config.RSI_LONG_PERIOD}'
        })
        # 売りシグナル出力ファイルのパスを設定
        sell_output_file = os.path.join(output_dir, "signal_result_sell.csv")
        
        # 結果をCSVファイルに出力
        # index=False: インデックスは出力しない（必要な情報のみをクリーンに出力）
        buy_signals.to_csv(buy_output_file, index=False)
        sell_signals.to_csv(sell_output_file, index=False)
        
        # 処理結果のログ出力
        # 何件のシグナルが検出され、どのファイルに出力されたかを記録
        logger.info(f"Buyシグナル: {len(buy_signals)}件を {buy_output_file} に出力しました")
        logger.info(f"Sellシグナル: {len(sell_signals)}件を {sell_output_file} に出力しました")
        
        # 処理成功を示す戻り値
        return True
        
    except Exception as e:
        # 例外発生時のエラーハンドリング
        # どのような例外が発生しても、エラーログを出力して処理失敗を返す
        logger.error(f"シグナル抽出処理中にエラーが発生しました: {str(e)}")
        return False

# このファイルが直接実行された場合（モジュールとしてインポートされた場合は実行されない）
if __name__ == "__main__":
    import sys
    import argparse
    
    # コマンドライン引数の解析
    # --testフラグによりテストモードが指定可能
    parser = argparse.ArgumentParser(description='Buy/Sellシグナル抽出ツール')
    parser.add_argument('--test', action='store_true', help='テストモードで実行')
    args = parser.parse_args()
    
    # ロガーの設定（data_loaderモジュールの関数を使用）
    # テストモードフラグを渡して適切なログ設定を行う
    from data_loader import setup_logger
    logger = setup_logger(args.test)
    
    # シグナル抽出処理の実行
    # args.testの値（True/False）をそのままextract_signals関数に渡す
    success = extract_signals(args.test)
    
    # 処理結果に応じた終了コードでプログラム終了
    # 成功時は0、失敗時は1を返す（Unix/Linuxの慣例に従う）
    sys.exit(0 if success else 1)