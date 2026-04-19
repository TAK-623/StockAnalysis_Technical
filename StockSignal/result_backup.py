"""
結果ファイルのバックアップ機能を提供するモジュール

このモジュールは、前回の実行結果をバックアップし、
連続該当銘柄の判定に必要な機能を提供します。
"""
import os
import shutil
import pandas as pd
from typing import Dict, Set, Tuple

def backup_previous_results():
    """
    前回の結果ファイルをバックアップする

    StockSignal/Result/ にある Breakout.csv / AllAbove.csv / push_mark.csv を
    StockSignal/Result/Previous/ にコピーします。
    """
    # 結果ディレクトリのパス
    result_dir = os.path.join(os.path.dirname(__file__), "Result")
    previous_dir = os.path.join(result_dir, "Previous")

    # Previousディレクトリが存在しない場合は作成
    if not os.path.exists(previous_dir):
        os.makedirs(previous_dir)
        print(f"Previousディレクトリを作成しました: {previous_dir}")

    # バックアップ対象ファイル
    files_to_backup = ["Breakout.csv", "AllAbove.csv", "push_mark.csv"]
    
    for file_name in files_to_backup:
        source_path = os.path.join(result_dir, file_name)
        dest_path = os.path.join(previous_dir, file_name)
        
        # ファイルが存在する場合のみバックアップ
        if os.path.exists(source_path):
            try:
                shutil.copy2(source_path, dest_path)
                print(f"バックアップ完了: {file_name}")
            except Exception as e:
                print(f"バックアップエラー ({file_name}): {e}")
        else:
            print(f"バックアップ対象ファイルが存在しません: {file_name}")

def get_consecutive_tickers() -> Dict[str, Set[str]]:
    """
    連続該当銘柄を特定する

    Returns:
        Dict[str, Set[str]]: カテゴリ別の連続該当銘柄セット
            - 'breakout': ブレイク銘柄で連続該当の銘柄セット
            - 'all_above': AllAbove銘柄で連続該当の銘柄セット
            - 'push_mark': 押し目買い銘柄で連続該当の銘柄セット
    """
    result_dir = os.path.join(os.path.dirname(__file__), "Result")
    previous_dir = os.path.join(result_dir, "Previous")

    consecutive_tickers = {
        'breakout': set(),
        'all_above': set(),
        'push_mark': set()
    }

    # カテゴリとファイル名の対応
    categories = [
        ('breakout', 'Breakout.csv', 'ブレイク'),
        ('all_above', 'AllAbove.csv', 'AllAbove'),
        ('push_mark', 'push_mark.csv', '押し目買い'),
    ]

    for key, file_name, label in categories:
        current_path = os.path.join(result_dir, file_name)
        previous_path = os.path.join(previous_dir, file_name)

        if os.path.exists(current_path) and os.path.exists(previous_path):
            try:
                current_df = pd.read_csv(current_path)
                previous_df = pd.read_csv(previous_path)

                current_tickers = set(current_df['Ticker'].astype(str))
                previous_tickers = set(previous_df['Ticker'].astype(str))

                consecutive_tickers[key] = current_tickers.intersection(previous_tickers)
                print(f"{label}銘柄連続該当数: {len(consecutive_tickers[key])}")
            except Exception as e:
                print(f"{label}銘柄連続該当チェックエラー: {e}")

    return consecutive_tickers

def decorate_company_name(ticker: str, company_name: str, consecutive_tickers: Dict[str, Set[str]]) -> str:
    """
    連続該当銘柄の場合、銘柄名の先頭に「◎」を付与する
    
    Args:
        ticker (str): 銘柄コード
        company_name (str): 銘柄名
        consecutive_tickers (Dict[str, Set[str]]): 連続該当銘柄セット
        
    Returns:
        str: 装飾された銘柄名
    """
    ticker_str = str(ticker)

    # いずれかのカテゴリで連続該当している場合
    if (ticker_str in consecutive_tickers.get('breakout', set()) or
        ticker_str in consecutive_tickers.get('all_above', set()) or
        ticker_str in consecutive_tickers.get('push_mark', set())):
        return f"◎{company_name}"

    return company_name
