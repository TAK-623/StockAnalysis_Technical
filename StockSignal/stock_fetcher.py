"""
株価取得モジュール - yfinanceを使用して株価データを取得します
このモジュールは、Yahoo Finance APIラッパーであるyfinanceライブラリを使用して
複数の銘柄の株価データを効率的に取得します。APIレート制限を考慮してバッチ処理を行い、
取得したデータはCSVファイルとして保存します。テストモードと通常モードの両方に対応しています。
"""
import os
import time
import pandas as pd
import yfinance as yf
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

def fetch_stock_data(tickers: List[str], batch_size: int = None, is_test_mode: bool = False) -> Dict[str, Optional[pd.DataFrame]]:
    """
    指定された銘柄コードリストに対して、バッチ処理で株価データを取得します
    
    複数の銘柄について、Yahoo Financeから株価データを取得します。
    APIレート制限を回避するためにバッチ処理を行い、各バッチおよび各銘柄間に
    待機時間を設けています。取得したデータはCSVファイルとして保存され、
    辞書形式でも返されます。データ取得に失敗した銘柄は辞書内でNone値となります。
    
    Args:
        tickers (List[str]): 取得対象の銘柄コードのリスト
        batch_size (int, optional): 一度に処理する銘柄の数。指定がない場合はconfig.BATCH_SIZEを使用
        is_test_mode (bool, optional): テストモードで実行するかどうか。デフォルトはFalse
        
    Returns:
        Dict[str, Optional[pd.DataFrame]]: 銘柄コードをキー、株価データのDataFrameを値とする辞書
                                          データ取得に失敗した場合は値がNoneとなる
    """
    import config  # 設定値モジュールをインポート
    
    # StockSignal名前付きロガーを取得
    logger = logging.getLogger("StockSignal")
    
    # 各銘柄の株価データを格納する辞書を初期化
    stock_data = {}
    
    # batch_sizeが指定されていない場合はconfig.pyから取得
    # APIレート制限を考慮した適切な値をconfigで管理
    if batch_size is None:
        batch_size = config.BATCH_SIZE
    
    # 保存用ディレクトリの設定と作成
    # テストモードの場合は別ディレクトリに保存
    data_dir = config.TEST_RESULT_DIR if is_test_mode else config.RESULT_DIR
    os.makedirs(data_dir, exist_ok=True)  # ディレクトリが存在しない場合は作成
    
    # 処理開始ログ
    logger.info(f"株価データの取得を開始します。対象企業数: {len(tickers)}")
    logger.info(f"取得期間: {config.HISTORY_PERIOD}")
    
    # バッチ処理のメインループ
    # tickers配列をbatch_size単位で分割して処理
    for i in range(0, len(tickers), batch_size):
        # 現在のバッチの銘柄リストを取得
        batch_tickers = tickers[i:i+batch_size]
        
        # 現在のバッチ処理状況をログ出力
        logger.info(f"バッチ処理: {i+1}～{min(i+batch_size, len(tickers))}社 ({len(tickers)}社中)")
        
        # バッチ内の各銘柄に対する処理
        for ticker in batch_tickers:
            try:
                # 日本の銘柄コードにYahoo Finance用のサフィックス(.T)を付加
                # 既にサフィックスがある場合は付加しない
                yf_ticker = f"{ticker}{config.YF_SUFFIX}" if not ticker.endswith(config.YF_SUFFIX) else ticker
                logger.info(f"銘柄 {ticker} の株価データを取得中...")
                
                # yfinanceライブラリを使用して銘柄情報オブジェクトを取得
                stock = yf.Ticker(yf_ticker)
                
                # 指定された期間の株価履歴データを取得
                # periodパラメータはconfig.HISTORY_PERIODで設定（例: "6mo"=6ヶ月）
                hist = stock.history(period=config.HISTORY_PERIOD)
                
                # 取得したデータが空の場合（銘柄が存在しない、データが無いなど）
                if hist.empty:
                    logger.warning(f"銘柄 {ticker} のデータが取得できませんでした")
                    stock_data[ticker] = None  # 辞書にはNoneを格納
                    continue  # 次の銘柄へスキップ
                
                # 取得したデータをCSVファイルとして保存
                csv_path = os.path.join(data_dir, f"{ticker}.csv")
                hist.to_csv(csv_path)
                logger.info(f"銘柄 {ticker} のデータを保存しました")
                
                # 結果辞書に株価データを格納
                stock_data[ticker] = hist
                
                # 銘柄間の待機時間を設定
                # APIへの連続リクエストによる制限を避けるため
                time.sleep(config.TICKER_WAIT_TIME)
                
            except Exception as e:
                # データ取得中に例外が発生した場合のエラーハンドリング
                logger.error(f"銘柄 {ticker} のデータ取得中にエラーが発生しました: {str(e)}")
                stock_data[ticker] = None  # 辞書にはNoneを格納
        
        # バッチ処理完了後、次のバッチへ進む前に待機（APIレート制限対策）
        # 最後のバッチの場合は待機しない
        if i + batch_size < len(tickers):
            logger.info(f"API制限を避けるために{config.BATCH_WAIT_TIME}秒間待機します...")
            time.sleep(config.BATCH_WAIT_TIME)
    
    # 全体の処理結果をログ出力
    # 成功・失敗した銘柄数をカウントして表示
    logger.info(f"株価データの取得が完了しました。成功: {sum(1 for v in stock_data.values() if v is not None)}社, 失敗: {sum(1 for v in stock_data.values() if v is None)}社")
    
    return stock_data