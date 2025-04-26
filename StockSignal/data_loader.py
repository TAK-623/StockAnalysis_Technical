"""
データローダーモジュール - CSVファイルから企業リストを読み込みます
このモジュールは、株価データ取得システムで使用する企業リストの読み込みと
ロギング設定のセットアップを担当します。テストモードと通常モードの両方に対応し、
適切なファイルパスとログ設定を提供します。
"""
import os
import pandas as pd
import logging
from typing import List, Optional

def setup_logger(is_test_mode=False):
    """
    アプリケーション全体で使用するロガーをセットアップします
    
    ファイルとコンソール両方への出力を設定し、テストモードに応じてログの出力先を変更します。
    
    Args:
        is_test_mode (bool): テストモードの場合はTrue、通常モードの場合はFalse
        
    Returns:
        logging.Logger: 設定済みのロガーインスタンス
    """
    import config  # ログファイルパスなどの設定値を取得
    
    # テストモードに応じてログディレクトリを設定
    # テストモード時は別ディレクトリにログを出力することでテスト実行の影響を隔離
    log_dir = config.TEST_LOG_DIR if is_test_mode else config.LOG_DIR
    
    # ログディレクトリがない場合は作成
    # exist_ok=Trueにより、既にディレクトリが存在する場合はエラーにならない
    os.makedirs(log_dir, exist_ok=True)
    
    # ログファイルパスの設定
    # config.LOG_FILE_NAMEには日付が含まれており、日ごとに新しいログファイルが作成される
    log_file = os.path.join(log_dir, config.LOG_FILE_NAME)
    
    # ロガーの設定
    # 名前付きロガー"StockSignal"を使用することで、アプリケーション全体で同じロガーを参照可能
    logger = logging.getLogger("StockSignal")
    logger.setLevel(logging.INFO)  # INFO以上のレベルのログをすべて記録
    
    # 既存のハンドラをクリア
    # 同じロガーが複数回初期化された場合に、ハンドラが重複して追加されることを防止
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # ファイルハンドラの設定
    # ログをファイルに出力するためのハンドラ、UTF-8エンコーディングを使用して日本語も正しく記録
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # コンソールハンドラの設定
    # ログをコンソール（標準出力）にも出力するためのハンドラ
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # フォーマッタの設定
    # ログの各行の形式を定義：時刻 - ロガー名 - ログレベル - メッセージ
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # ハンドラをロガーに追加
    # これにより同じログがファイルとコンソールの両方に出力される
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def load_company_list(is_test_mode: bool = False) -> List[str]:
    """
    企業リストCSVファイルから銘柄コードのリストを読み込みます
    
    テストモードに応じて読み込むファイルを変更し、CSVのフォーマットを検証した上で
    銘柄コードのリストを返します。エラーが発生した場合は空のリストを返します。
    
    Args:
        is_test_mode (bool): テストモードの場合はTrue、通常モードの場合はFalse
        
    Returns:
        List[str]: 銘柄コードのリスト。エラー時は空リスト。
    """
    import config  # ファイルパスなどの設定値を取得
    
    # StockSignal名前付きロガーを取得
    # setup_logger関数で設定済みのロガーインスタンスを参照
    logger = logging.getLogger("StockSignal")
    
    try:
        # テストモードに応じてファイルパスを設定
        if is_test_mode:
            # テストモード: 少数の銘柄を含むテスト用CSVファイルを使用
            file_path = os.path.join(config.TEST_DIR, config.COMPANY_LIST_TEST_FILE)
            logger.info(f"テストモード: {file_path} からデータを読み込みます")
        else:
            # 通常モード: 本番用の全銘柄を含むCSVファイルを使用
            file_path = os.path.join(config.BASE_DIR, config.COMPANY_LIST_FILE)
            logger.info(f"通常モード: {file_path} からデータを読み込みます")
        
        # ファイルの存在チェック
        # ファイルが存在しない場合はエラーログを出力して空リストを返す
        if not os.path.exists(file_path):
            logger.error(f"ファイルが見つかりません: {file_path}")
            return []
        
        # CSVファイルの読み込み
        # UTF-8エンコーディングを指定してpandasでCSVを読み込む
        df = pd.read_csv(file_path, encoding='utf-8')
        
        # 'Ticker'列の存在チェック
        # CSVファイルのフォーマットが正しいかを検証
        if 'Ticker' not in df.columns:
            logger.error(f"'Ticker'列がCSVファイルに見つかりません: {file_path}")
            return []
        
        # 銘柄コードのリストを取得
        # Ticker列の値をリストとして抽出
        tickers = df['Ticker'].tolist()
        logger.info(f"{len(tickers)}社の銘柄コードを読み込みました")
        
        return tickers
        
    except Exception as e:
        # 読み込み中のあらゆる例外をキャッチし、エラーログを出力
        # ファイル形式の問題、エンコーディングの問題などのあらゆるエラーに対応
        logger.error(f"企業リストの読み込み中にエラーが発生しました: {str(e)}")
        return []