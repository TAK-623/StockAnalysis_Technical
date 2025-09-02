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
    
    StockSignal/Result/ にある Breakout.csv と push_mark.csv を
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
    files_to_backup = ["Breakout.csv", "push_mark.csv"]
    
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
            - 'push_mark': 押し目買い銘柄で連続該当の銘柄セット
    """
    result_dir = os.path.join(os.path.dirname(__file__), "Result")
    previous_dir = os.path.join(result_dir, "Previous")
    
    consecutive_tickers = {
        'breakout': set(),
        'push_mark': set()
    }
    
    # ブレイク銘柄の連続該当をチェック
    current_breakout_path = os.path.join(result_dir, "Breakout.csv")
    previous_breakout_path = os.path.join(previous_dir, "Breakout.csv")
    
    if os.path.exists(current_breakout_path) and os.path.exists(previous_breakout_path):
        try:
            current_breakout = pd.read_csv(current_breakout_path)
            previous_breakout = pd.read_csv(previous_breakout_path)
            
            current_tickers = set(current_breakout['Ticker'].astype(str))
            previous_tickers = set(previous_breakout['Ticker'].astype(str))
            
            consecutive_tickers['breakout'] = current_tickers.intersection(previous_tickers)
            print(f"ブレイク銘柄連続該当数: {len(consecutive_tickers['breakout'])}")
        except Exception as e:
            print(f"ブレイク銘柄連続該当チェックエラー: {e}")
    
    # 押し目買い銘柄の連続該当をチェック
    current_push_mark_path = os.path.join(result_dir, "push_mark.csv")
    previous_push_mark_path = os.path.join(previous_dir, "push_mark.csv")
    
    if os.path.exists(current_push_mark_path) and os.path.exists(previous_push_mark_path):
        try:
            current_push_mark = pd.read_csv(current_push_mark_path)
            previous_push_mark = pd.read_csv(previous_push_mark_path)
            
            current_tickers = set(current_push_mark['Ticker'].astype(str))
            previous_tickers = set(previous_push_mark['Ticker'].astype(str))
            
            consecutive_tickers['push_mark'] = current_tickers.intersection(previous_tickers)
            print(f"押し目買い銘柄連続該当数: {len(consecutive_tickers['push_mark'])}")
        except Exception as e:
            print(f"押し目買い銘柄連続該当チェックエラー: {e}")
    
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
    
    # ブレイク銘柄または押し目買い銘柄で連続該当の場合
    if (ticker_str in consecutive_tickers.get('breakout', set()) or 
        ticker_str in consecutive_tickers.get('push_mark', set())):
        return f"◎{company_name}"
    
    return company_name
