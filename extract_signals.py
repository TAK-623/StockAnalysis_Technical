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
    MACD-RSIとMACD-RCIの両方のシグナルを抽出します。
    また、両方のシグナルが一致している銘柄も別途抽出します。
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
        # RCI長期の列名を取得（config.RCI_LONG_PERIODの値に基づく）
        rci_long_col = f'RCI{config.RCI_LONG_PERIOD}'
        
        # 必要なカラムの存在確認
        # データフレームに必要なカラムが含まれているか検証
        required_columns = ['Ticker', 'Company', 'MACD-RSI', 'MACD-RCI', 'Close', 'MACD', rsi_long_col, rci_long_col]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            # 必要なカラムが見つからない場合はエラーログを出力して処理を中断
            logger.error(f"必要なカラムがCSVファイルに見つかりません: {missing_columns}")
            return False
        
        # === MACD-RSI シグナル処理 ===
        # Buyシグナルの抽出処理
        # 1. MACD-RSIカラムが'Buy'のレコードのみを抽出
        # 2. 必要なカラム（銘柄コード、会社名、終値、MACD、RSI長期）のみを選択
        macd_rsi_buy_signals = df[df['MACD-RSI'] == 'Buy'][['Ticker', 'Company', 'Close', 'MACD', rsi_long_col]]
        
        # 数値データの小数点以下桁数を調整（小数点以下2桁に丸める）
        macd_rsi_buy_signals['MACD'] = macd_rsi_buy_signals['MACD'].round(2)
        macd_rsi_buy_signals[rsi_long_col] = macd_rsi_buy_signals[rsi_long_col].round(2)
        
        # カラム名を日本語に変更（レポートの可読性向上のため）
        macd_rsi_buy_signals = macd_rsi_buy_signals.rename(columns={
            'Close': '終値',
            'MACD': 'MACD',
            rsi_long_col: f'RSI{config.RSI_LONG_PERIOD}'
        })
        # 買いシグナル出力ファイルのパスを設定
        macd_rsi_buy_output_file = os.path.join(output_dir, "macd_rsi_signal_result_buy.csv")
        
        # Sellシグナルの抽出処理
        # 1. MACD-RSIカラムが'Sell'のレコードのみを抽出
        # 2. 必要なカラム（銘柄コード、会社名、終値、MACD、RSI長期）のみを選択
        macd_rsi_sell_signals = df[df['MACD-RSI'] == 'Sell'][['Ticker', 'Company', 'Close', 'MACD', rsi_long_col]]
        
        # 数値データの小数点以下桁数を調整
        macd_rsi_sell_signals['MACD'] = macd_rsi_sell_signals['MACD'].round(2)
        macd_rsi_sell_signals[rsi_long_col] = macd_rsi_sell_signals[rsi_long_col].round(2)
        
        # 終値の表示形式を調整（小数点以下が0の場合は整数表示、それ以外は小数点以下1桁）
        macd_rsi_sell_signals['Close'] = macd_rsi_sell_signals['Close'].apply(
            lambda x: int(x) if x == int(x) else round(x, 1)
        )
        
        # カラム名を日本語に変更（レポートの可読性向上のため）
        macd_rsi_sell_signals = macd_rsi_sell_signals.rename(columns={
            'Close': '終値',
            'MACD': 'MACD',
            rsi_long_col: f'RSI{config.RSI_LONG_PERIOD}'
        })
        # 売りシグナル出力ファイルのパスを設定
        macd_rsi_sell_output_file = os.path.join(output_dir, "macd_rsi_signal_result_sell.csv")
        
        # 結果をCSVファイルに出力
        # index=False: インデックスは出力しない（必要な情報のみをクリーンに出力）
        macd_rsi_buy_signals.to_csv(macd_rsi_buy_output_file, index=False)
        macd_rsi_sell_signals.to_csv(macd_rsi_sell_output_file, index=False)
        
        # 処理結果のログ出力
        # 何件のシグナルが検出され、どのファイルに出力されたかを記録
        logger.info(f"MACD-RSI Buyシグナル: {len(macd_rsi_buy_signals)}件を {macd_rsi_buy_output_file} に出力しました")
        logger.info(f"MACD-RSI Sellシグナル: {len(macd_rsi_sell_signals)}件を {macd_rsi_sell_output_file} に出力しました")
        
        # === MACD-RCI シグナル処理 ===
        # Buyシグナルの抽出処理
        # 1. MACD-RCIカラムが'Buy'のレコードのみを抽出
        # 2. 必要なカラム（銘柄コード、会社名、終値、MACD、RCI長期）のみを選択
        macd_rci_buy_signals = df[df['MACD-RCI'] == 'Buy'][['Ticker', 'Company', 'Close', 'MACD', rci_long_col]]
        
        # 数値データの小数点以下桁数を調整（小数点以下2桁に丸める）
        macd_rci_buy_signals['MACD'] = macd_rci_buy_signals['MACD'].round(2)
        macd_rci_buy_signals[rci_long_col] = macd_rci_buy_signals[rci_long_col].round(2)
        
        # カラム名を日本語に変更（レポートの可読性向上のため）
        macd_rci_buy_signals = macd_rci_buy_signals.rename(columns={
            'Close': '終値',
            'MACD': 'MACD',
            rci_long_col: f'RCI{config.RCI_LONG_PERIOD}'
        })
        # 買いシグナル出力ファイルのパスを設定
        macd_rci_buy_output_file = os.path.join(output_dir, "macd_rci_signal_result_buy.csv")
        
        # Sellシグナルの抽出処理
        # 1. MACD-RCIカラムが'Sell'のレコードのみを抽出
        # 2. 必要なカラム（銘柄コード、会社名、終値、MACD、RCI長期）のみを選択
        macd_rci_sell_signals = df[df['MACD-RCI'] == 'Sell'][['Ticker', 'Company', 'Close', 'MACD', rci_long_col]]
        
        # 数値データの小数点以下桁数を調整
        macd_rci_sell_signals['MACD'] = macd_rci_sell_signals['MACD'].round(2)
        macd_rci_sell_signals[rci_long_col] = macd_rci_sell_signals[rci_long_col].round(2)
        
        # 終値の表示形式を調整（小数点以下が0の場合は整数表示、それ以外は小数点以下1桁）
        macd_rci_sell_signals['Close'] = macd_rci_sell_signals['Close'].apply(
            lambda x: int(x) if x == int(x) else round(x, 1)
        )
        
        # カラム名を日本語に変更（レポートの可読性向上のため）
        macd_rci_sell_signals = macd_rci_sell_signals.rename(columns={
            'Close': '終値',
            'MACD': 'MACD',
            rci_long_col: f'RCI{config.RCI_LONG_PERIOD}'
        })
        # 売りシグナル出力ファイルのパスを設定
        macd_rci_sell_output_file = os.path.join(output_dir, "macd_rci_signal_result_sell.csv")
        
        # 結果をCSVファイルに出力
        # index=False: インデックスは出力しない（必要な情報のみをクリーンに出力）
        macd_rci_buy_signals.to_csv(macd_rci_buy_output_file, index=False)
        macd_rci_sell_signals.to_csv(macd_rci_sell_output_file, index=False)
        
        # 処理結果のログ出力
        # 何件のシグナルが検出され、どのファイルに出力されたかを記録
        logger.info(f"MACD-RCI Buyシグナル: {len(macd_rci_buy_signals)}件を {macd_rci_buy_output_file} に出力しました")
        logger.info(f"MACD-RCI Sellシグナル: {len(macd_rci_sell_signals)}件を {macd_rci_sell_output_file} に出力しました")
        
        # === 両シグナル一致（MACD-RSIとMACD-RCIが両方とも同じシグナル）を抽出 ===
        # 両方がBuyの銘柄を抽出
        macd_rsi_rci_buy_signals = df[(df['MACD-RSI'] == 'Buy') & (df['MACD-RCI'] == 'Buy')]
        
        # 必要なカラムのみを選択（両方のシグナルに使用されている指標を含める）
        both_buy_columns = ['Ticker', 'Company', 'Close', 'MACD', rsi_long_col, rci_long_col]
        macd_rsi_rci_buy_signals = macd_rsi_rci_buy_signals[both_buy_columns]
        
        # 数値データの小数点以下桁数を調整
        macd_rsi_rci_buy_signals['MACD'] = macd_rsi_rci_buy_signals['MACD'].round(2)
        macd_rsi_rci_buy_signals[rsi_long_col] = macd_rsi_rci_buy_signals[rsi_long_col].round(2)
        macd_rsi_rci_buy_signals[rci_long_col] = macd_rsi_rci_buy_signals[rci_long_col].round(2)
        
        # カラム名を日本語に変更
        macd_rsi_rci_buy_signals = macd_rsi_rci_buy_signals.rename(columns={
            'Close': '終値',
            'MACD': 'MACD',
            rsi_long_col: f'RSI{config.RSI_LONG_PERIOD}',
            rci_long_col: f'RCI{config.RCI_LONG_PERIOD}'
        })
        
        # 両方がBuyの出力ファイルパスを設定
        macd_rsi_rci_buy_output_file = os.path.join(output_dir, "macd_rsi_rci_signal_result_buy.csv")
        
        # 両方がSellの銘柄を抽出
        macd_rsi_rci_sell_signals = df[(df['MACD-RSI'] == 'Sell') & (df['MACD-RCI'] == 'Sell')]
        
        # 必要なカラムのみを選択
        both_sell_columns = ['Ticker', 'Company', 'Close', 'MACD', rsi_long_col, rci_long_col]
        macd_rsi_rci_sell_signals = macd_rsi_rci_sell_signals[both_sell_columns]
        
        # 数値データの小数点以下桁数を調整
        macd_rsi_rci_sell_signals['MACD'] = macd_rsi_rci_sell_signals['MACD'].round(2)
        macd_rsi_rci_sell_signals[rsi_long_col] = macd_rsi_rci_sell_signals[rsi_long_col].round(2)
        macd_rsi_rci_sell_signals[rci_long_col] = macd_rsi_rci_sell_signals[rci_long_col].round(2)
        
        # 終値の表示形式を調整
        macd_rsi_rci_sell_signals['Close'] = macd_rsi_rci_sell_signals['Close'].apply(
            lambda x: int(x) if x == int(x) else round(x, 1)
        )
        
        # カラム名を日本語に変更
        macd_rsi_rci_sell_signals = macd_rsi_rci_sell_signals.rename(columns={
            'Close': '終値',
            'MACD': 'MACD',
            rsi_long_col: f'RSI{config.RSI_LONG_PERIOD}',
            rci_long_col: f'RCI{config.RCI_LONG_PERIOD}'
        })
        
        # 両方がSellの出力ファイルパスを設定
        macd_rsi_rci_sell_output_file = os.path.join(output_dir, "macd_rsi_rci_signal_result_sell.csv")
        
        # 結果をCSVファイルに出力
        macd_rsi_rci_buy_signals.to_csv(macd_rsi_rci_buy_output_file, index=False)
        macd_rsi_rci_sell_signals.to_csv(macd_rsi_rci_sell_output_file, index=False)
        
        # 処理結果のログ出力
        logger.info(f"両方Buy（MACD-RSI・MACD-RCI）シグナル: {len(macd_rsi_rci_buy_signals)}件を {macd_rsi_rci_buy_output_file} に出力しました")
        logger.info(f"両方Sell（MACD-RSI・MACD-RCI）シグナル: {len(macd_rsi_rci_sell_signals)}件を {macd_rsi_rci_sell_output_file} に出力しました")
        
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