"""
データローダーモジュール - ローカルメタデータ（企業リスト、ロガー設定）の読み込み

このモジュールは、ローカルに存在する静的なメタデータの読み込みを担当します。
外部APIから取得する株価データ（stock_fetcher.py）とは責務を分けています。

主な機能：
- ロガーのセットアップ（ファイル・コンソール両方への出力）
- 企業リストCSVファイルの読み込み（ticker一覧・企業情報マップの2形式）
- テストモード/通常モードの切り替え対応
"""
import os
import pandas as pd
import logging
from typing import List, Dict


def setup_logger(is_test_mode: bool = False) -> logging.Logger:
    """
    アプリケーション全体で使用するロガーをセットアップします

    ファイルとコンソール両方への出力を設定し、テストモードに応じてログの出力先を変更します。
    ログレベルはINFO以上で、日付・時刻・ロガー名・レベル・メッセージの形式で出力されます。

    Args:
        is_test_mode: テストモード時は別ディレクトリにログを出力

    Returns:
        logging.Logger: 設定済みのロガーインスタンス
    """
    import config

    # テストモードに応じてログディレクトリを設定
    log_dir = config.TEST_LOG_DIR if is_test_mode else config.LOG_DIR
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, config.LOG_FILE_NAME)

    # 名前付きロガー "StockSignal" でアプリ全体から参照
    logger = logging.getLogger("StockSignal")
    logger.setLevel(logging.INFO)

    # 重複登録防止
    if logger.hasHandlers():
        logger.handlers.clear()

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def _read_company_csv(is_test_mode: bool = False) -> pd.DataFrame:
    """
    企業リストCSVを読み込み、DataFrameとして返します（内部関数）

    load_company_list / load_company_info_map の共通基盤として、
    CSV読み込みとフォーマット検証を一箇所に集約します。

    Args:
        is_test_mode: テストモード時は少数銘柄のテスト用CSVファイルを使用

    Returns:
        pd.DataFrame: 企業リストのDataFrame。エラー時は空のDataFrame。
    """
    import config

    logger = logging.getLogger("StockSignal")

    if is_test_mode:
        file_path = os.path.join(config.TEST_DIR, config.COMPANY_LIST_TEST_FILE)
        logger.info(f"テストモード: {file_path} からデータを読み込みます")
    else:
        file_path = os.path.join(config.BASE_DIR, config.COMPANY_LIST_FILE)
        logger.info(f"通常モード: {file_path} からデータを読み込みます")

    if not os.path.exists(file_path):
        logger.error(f"ファイルが見つかりません: {file_path}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except Exception as e:
        logger.error(f"企業リストの読み込み中にエラーが発生しました: {str(e)}")
        return pd.DataFrame()

    if 'Ticker' not in df.columns:
        logger.error(f"'Ticker'列がCSVファイルに見つかりません: {file_path}")
        return pd.DataFrame()

    return df


def load_company_list(is_test_mode: bool = False) -> List[str]:
    """
    企業リストCSVファイルから銘柄コードのリストを読み込みます

    Args:
        is_test_mode: テストモード時は少数銘柄のテスト用CSVファイルを使用

    Returns:
        List[str]: 銘柄コードのリスト。エラー時は空リスト。
    """
    df = _read_company_csv(is_test_mode)
    if df.empty:
        return []

    logger = logging.getLogger("StockSignal")
    tickers = df['Ticker'].tolist()
    logger.info(f"{len(tickers)}社の銘柄コードを読み込みました")
    return tickers


def load_company_info_map(is_test_mode: bool = False) -> Dict[str, Dict[str, str]]:
    """
    銘柄コードから会社名とテーマへのマッピングを取得します

    ブレイクアウト・押し目銘柄の結果ファイルに会社情報を付加するために使用されます。

    Args:
        is_test_mode: テストモード時は別のCSVファイルを使用

    Returns:
        Dict[str, Dict[str, str]]: 銘柄コードをキー、
            {'company': 会社名, 'theme': テーマ}を値とする辞書。
            エラー時は空の辞書。
    """
    df = _read_company_csv(is_test_mode)
    company_info_map: Dict[str, Dict[str, str]] = {}

    if df.empty:
        return company_info_map

    logger = logging.getLogger("StockSignal")

    required_columns = ['Ticker', '銘柄名', 'テーマ']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logger.error(f"企業リストに必要なカラムがありません: {missing_columns}")
        return company_info_map

    for _, row in df.iterrows():
        ticker_str = str(row['Ticker'])
        company_info_map[ticker_str] = {
            'company': row['銘柄名'],
            'theme': row['テーマ']
        }

    logger.info(f"{len(company_info_map)}社の会社情報マッピング（会社名・テーマ）を読み込みました")
    return company_info_map
