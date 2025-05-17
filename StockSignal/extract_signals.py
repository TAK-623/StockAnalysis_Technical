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
    
    追加条件：
    - 買いシグナル：CloseがHighとLowの中間よりも上にある（上髭が短い銘柄）
    - 売りシグナル：CloseがHighとLowの中間よりも下にある（下髭が短い銘柄）
    
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
            input_dir = os.path.join(config.BASE_DIR, "StockSignal", "TechnicalSignal")
        
        # 入力ファイルのフルパスを生成 (latest_signal.csv)
        input_file = os.path.join(input_dir, config.LATEST_SIGNAL_FILE)
        
        # 出力ディレクトリの設定
        # テストモードと通常モードで異なる出力先を使用
        if is_test_mode:
            # テストモード: テスト用ディレクトリ内のResultフォルダに出力
            output_dir = os.path.join(config.TEST_DIR, "Result")
        else:
            # 通常モード: 本番用ディレクトリ内のResultフォルダに出力
            output_dir = os.path.join(config.BASE_DIR, "StockSignal", "Result")
        
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
        # RCI短期の列名を取得（config.RCI_SHORT_PERIODの値に基づく）
        rci_short_col = f'RCI{config.RCI_SHORT_PERIOD}'
        # RCI長期の列名を取得（config.RCI_LONG_PERIODの値に基づく）
        rci_long_col = f'RCI{config.RCI_LONG_PERIOD}'
        
        # 必要なカラムの存在確認
        # データフレームに必要なカラムが含まれているか検証
        # 新たに High と Low を必要なカラムに追加（フィルタリングに使用するため）
        required_columns = ['Ticker', 'Company', 'MACD-RSI', 'MACD-RCI', 'Close', 'High', 'Low', 'MACD', rsi_long_col, rci_long_col]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            # 必要なカラムが見つからない場合はエラーログを出力して処理を中断
            logger.error(f"必要なカラムがCSVファイルに見つかりません: {missing_columns}")
            return False
        
        # 高値と安値の中間値（ミッドポイント）を計算
        # これは、ロウソク足チャートの上髭/下髭を判断するための基準値となる
        df['Midpoint'] = (df['High'] + df['Low']) / 2
        
        # === MACD-RSI シグナル処理 ===
        # Buyシグナルの抽出処理
        # 1. MACD-RSIカラムが'Buy'のレコードのみを抽出
        # 2. 追加条件：終値が高値と安値の中間よりも上にある（上髭が短い銘柄）
        # 3. 必要なカラム（銘柄コード、会社名、終値、MACD、RSI長期）のみを選択
        macd_rsi_buy_signals = df[(df['MACD-RSI'] == 'Buy') & (df['Close'] > df['Midpoint'])]
        macd_rsi_buy_signals = macd_rsi_buy_signals[['Ticker', 'Company', 'Close', 'MACD', rsi_long_col]]
        
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
        # 2. 追加条件：終値が高値と安値の中間よりも下にある（下髭が短い銘柄）
        # 3. 必要なカラム（銘柄コード、会社名、終値、MACD、RSI長期）のみを選択
        macd_rsi_sell_signals = df[(df['MACD-RSI'] == 'Sell') & (df['Close'] < df['Midpoint'])]
        macd_rsi_sell_signals = macd_rsi_sell_signals[['Ticker', 'Company', 'Close', 'MACD', rsi_long_col]]
        
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
        logger.info(f"MACD-RSI Buyシグナル（Close > Midpoint条件付き）: {len(macd_rsi_buy_signals)}件を {macd_rsi_buy_output_file} に出力しました")
        logger.info(f"MACD-RSI Sellシグナル（Close < Midpoint条件付き）: {len(macd_rsi_sell_signals)}件を {macd_rsi_sell_output_file} に出力しました")
        
        # === MACD-RCI シグナル処理 ===
        # Buyシグナルの抽出処理
        # 1. MACD-RCIカラムが'Buy'のレコードのみを抽出
        # 2. 追加条件：終値が高値と安値の中間よりも上にある（上髭が短い銘柄）
        # 3. 必要なカラム（銘柄コード、会社名、終値、MACD、RCI短期、RCI長期）のみを選択
        macd_rci_buy_signals = df[(df['MACD-RCI'] == 'Buy') & (df['Close'] > df['Midpoint'])]
        macd_rci_buy_signals = macd_rci_buy_signals[['Ticker', 'Company', 'Close', 'MACD', rci_short_col, rci_long_col]]
        
        # 数値データの小数点以下桁数を調整（小数点以下2桁に丸める）
        macd_rci_buy_signals['MACD'] = macd_rci_buy_signals['MACD'].round(2)
        macd_rci_buy_signals[rci_short_col] = macd_rci_buy_signals[rci_short_col].round(2)
        macd_rci_buy_signals[rci_long_col] = macd_rci_buy_signals[rci_long_col].round(2)
        
        # カラム名を日本語に変更（レポートの可読性向上のため）
        macd_rci_buy_signals = macd_rci_buy_signals.rename(columns={
            'Close': '終値',
            'MACD': 'MACD',
            rci_short_col: f'RCI{config.RCI_SHORT_PERIOD}',
            rci_long_col: f'RCI{config.RCI_LONG_PERIOD}'
        })
        # 買いシグナル出力ファイルのパスを設定
        macd_rci_buy_output_file = os.path.join(output_dir, "macd_rci_signal_result_buy.csv")
        
        # Sellシグナルの抽出処理
        # 1. MACD-RCIカラムが'Sell'のレコードのみを抽出
        # 2. 追加条件：終値が高値と安値の中間よりも下にある（下髭が短い銘柄）
        # 3. 必要なカラム（銘柄コード、会社名、終値、MACD、RCI短期、RCI長期）のみを選択
        macd_rci_sell_signals = df[(df['MACD-RCI'] == 'Sell') & (df['Close'] < df['Midpoint'])]
        macd_rci_sell_signals = macd_rci_sell_signals[['Ticker', 'Company', 'Close', 'MACD', rci_short_col, rci_long_col]]
        
        # 数値データの小数点以下桁数を調整
        macd_rci_sell_signals['MACD'] = macd_rci_sell_signals['MACD'].round(2)
        macd_rci_sell_signals[rci_short_col] = macd_rci_sell_signals[rci_short_col].round(2)
        macd_rci_sell_signals[rci_long_col] = macd_rci_sell_signals[rci_long_col].round(2)
        
        # 終値の表示形式を調整（小数点以下が0の場合は整数表示、それ以外は小数点以下1桁）
        macd_rci_sell_signals['Close'] = macd_rci_sell_signals['Close'].apply(
            lambda x: int(x) if x == int(x) else round(x, 1)
        )
        
        # カラム名を日本語に変更（レポートの可読性向上のため）
        macd_rci_sell_signals = macd_rci_sell_signals.rename(columns={
            'Close': '終値',
            'MACD': 'MACD',
            rci_short_col: f'RCI{config.RCI_SHORT_PERIOD}',
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
        logger.info(f"MACD-RCI Buyシグナル（Close > Midpoint条件付き）: {len(macd_rci_buy_signals)}件を {macd_rci_buy_output_file} に出力しました")
        logger.info(f"MACD-RCI Sellシグナル（Close < Midpoint条件付き）: {len(macd_rci_sell_signals)}件を {macd_rci_sell_output_file} に出力しました")
        
        # === 両シグナル一致（MACD-RSIとMACD-RCIが両方とも同じシグナル）を抽出 ===
        # 両方がBuyの銘柄を抽出
        # 追加条件：終値が高値と安値の中間よりも上にある（上髭が短い銘柄）
        macd_rsi_rci_buy_signals = df[(df['MACD-RSI'] == 'Buy') & 
                                      (df['MACD-RCI'] == 'Buy') & 
                                      (df['Close'] > df['Midpoint'])]
        
        # 必要なカラムのみを選択（両方のシグナルに使用されている指標を含める）
        both_buy_columns = ['Ticker', 'Company', 'Close', 'MACD', rsi_long_col, rci_short_col, rci_long_col]
        macd_rsi_rci_buy_signals = macd_rsi_rci_buy_signals[both_buy_columns]
        
        # 数値データの小数点以下桁数を調整
        macd_rsi_rci_buy_signals['MACD'] = macd_rsi_rci_buy_signals['MACD'].round(2)
        macd_rsi_rci_buy_signals[rsi_long_col] = macd_rsi_rci_buy_signals[rsi_long_col].round(2)
        macd_rsi_rci_buy_signals[rci_short_col] = macd_rsi_rci_buy_signals[rci_short_col].round(2)
        macd_rsi_rci_buy_signals[rci_long_col] = macd_rsi_rci_buy_signals[rci_long_col].round(2)
        
        # カラム名を日本語に変更
        macd_rsi_rci_buy_signals = macd_rsi_rci_buy_signals.rename(columns={
            'Close': '終値',
            'MACD': 'MACD',
            rsi_long_col: f'RSI{config.RSI_LONG_PERIOD}',
            rci_short_col: f'RCI{config.RCI_SHORT_PERIOD}',
            rci_long_col: f'RCI{config.RCI_LONG_PERIOD}'
        })
        
        # 両方がBuyの出力ファイルパスを設定
        macd_rsi_rci_buy_output_file = os.path.join(output_dir, "macd_rsi_rci_signal_result_buy.csv")
        
        # 両方がSellの銘柄を抽出
        # 追加条件：終値が高値と安値の中間よりも下にある（下髭が短い銘柄）
        macd_rsi_rci_sell_signals = df[(df['MACD-RSI'] == 'Sell') & 
                                       (df['MACD-RCI'] == 'Sell') & 
                                       (df['Close'] < df['Midpoint'])]
        
        # 必要なカラムのみを選択
        both_sell_columns = ['Ticker', 'Company', 'Close', 'MACD', rsi_long_col, rci_short_col, rci_long_col]
        macd_rsi_rci_sell_signals = macd_rsi_rci_sell_signals[both_sell_columns]
        
        # 数値データの小数点以下桁数を調整
        macd_rsi_rci_sell_signals['MACD'] = macd_rsi_rci_sell_signals['MACD'].round(2)
        macd_rsi_rci_sell_signals[rsi_long_col] = macd_rsi_rci_sell_signals[rsi_long_col].round(2)
        macd_rsi_rci_sell_signals[rci_short_col] = macd_rsi_rci_sell_signals[rci_short_col].round(2)
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
            rci_short_col: f'RCI{config.RCI_SHORT_PERIOD}',
            rci_long_col: f'RCI{config.RCI_LONG_PERIOD}'
        })
        
        # 両方がSellの出力ファイルパスを設定
        macd_rsi_rci_sell_output_file = os.path.join(output_dir, "macd_rsi_rci_signal_result_sell.csv")
        
        # 結果をCSVファイルに出力
        macd_rsi_rci_buy_signals.to_csv(macd_rsi_rci_buy_output_file, index=False)
        macd_rsi_rci_sell_signals.to_csv(macd_rsi_rci_sell_output_file, index=False)
        
        # 処理結果のログ出力
        logger.info(f"両方Buy（MACD-RSI・MACD-RCI）シグナル（Close > Midpoint条件付き）: {len(macd_rsi_rci_buy_signals)}件を {macd_rsi_rci_buy_output_file} に出力しました")
        logger.info(f"両方Sell（MACD-RSI・MACD-RCI）シグナル（Close < Midpoint条件付き）: {len(macd_rsi_rci_sell_signals)}件を {macd_rsi_rci_sell_output_file} に出力しました")
        
        # 処理成功を示す戻り値
        return True
        
    except Exception as e:
        # 例外発生時のエラーハンドリング
        # どのような例外が発生しても、エラーログを出力して処理失敗を返す
        logger.error(f"シグナル抽出処理中にエラーが発生しました: {str(e)}")
        return False

def extract_strong_buying_trend(is_test_mode: bool = False) -> bool:
    """
    latest_signal.csvから強気トレンドの銘柄を抽出してCSVファイルに出力します
    
    以下の条件をすべて満たす銘柄を抽出します：
    1. 前の営業日の短期移動平均と中期移動平均の差分よりも、最新の短期移動平均と中期移動平均の差分の方が大きい
    2. 「短期移動平均 ＞ 中期移動平均 ＞ 長期移動平均」の関係が成立している
    3. 最新のClose値が短期移動平均よりも高い
    
    Args:
        is_test_mode (bool): テストモードの場合はTrue、通常モードの場合はFalse
        
    Returns:
        bool: 処理が成功した場合はTrue、エラーが発生した場合はFalse
    """
    import config  # 設定値モジュールをインポート
    
    # StockSignal名前付きロガーを取得
    logger = logging.getLogger("StockSignal")
    logger.info("強気トレンド銘柄の抽出を開始します")
    
    try:
        # 入力ファイルのパスを設定
        if is_test_mode:
            input_dir = os.path.join(config.TEST_DIR, "StockSignal", "TechnicalSignal")
        else:
            input_dir = os.path.join(config.BASE_DIR, "StockSignal", "TechnicalSignal")
        
        input_file = os.path.join(input_dir, config.LATEST_SIGNAL_FILE)
        
        # 出力ディレクトリの設定
        if is_test_mode:
            output_dir = os.path.join(config.TEST_DIR, "Result")
        else:
            output_dir = os.path.join(config.BASE_DIR, "StockSignal", "Result")
        
        # 出力ディレクトリが存在しない場合は作成
        os.makedirs(output_dir, exist_ok=True)
        
        # 入力ファイルの存在確認
        if not os.path.exists(input_file):
            logger.error(f"ファイルが見つかりません: {input_file}")
            return False
        
        # CSVの読み込み
        logger.info(f"{input_file} を読み込みます")
        df = pd.read_csv(input_file, index_col=0, parse_dates=True)
        
        # 各銘柄の短期・中期・長期の移動平均を取得
        # 設定ファイルから移動平均期間を取得 (MA_PERIODS = [5, 25, 75])
        short_ma = f'MA{config.MA_PERIODS[0]}'  # 短期移動平均 (MA5)
        mid_ma = f'MA{config.MA_PERIODS[1]}'    # 中期移動平均 (MA25)
        long_ma = f'MA{config.MA_PERIODS[2]}'   # 長期移動平均 (MA75)
        
        # 必要なカラムの存在確認
        required_columns = ['Ticker', 'Company', 'Close', short_ma, mid_ma, long_ma]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"必要なカラムがCSVファイルに見つかりません: {missing_columns}")
            return False
        
        # デバッグ出力: 各銘柄について条件2,3の結果を確認
        logger.info("各銘柄の条件判定を開始します")
        
        # 全銘柄のティッカーリストを取得
        all_tickers = df['Ticker'].unique()
        logger.info(f"処理対象の全銘柄数: {len(all_tickers)}")
        
        # 条件2: 短期MA > 中期MA > 長期MA の判定結果
        condition2 = (df[short_ma] > df[mid_ma]) & (df[mid_ma] > df[long_ma])
        
        # 条件3: 最新のClose値が短期移動平均よりも高い の判定結果
        condition3 = df['Close'] > df[short_ma]
        
        # 各銘柄の条件2と3の組み合わせ結果
        condition_results = condition2 & condition3
        
        # 条件2と3を満たす候補銘柄を抽出
        potential_tickers = df[condition_results]['Ticker'].unique()
        
        logger.info(f"条件2と3を満たす候補銘柄: {len(potential_tickers)}社を検出しました")
        if len(potential_tickers) > 0:
            logger.info(f"候補銘柄: {potential_tickers}")
        
        # 強気トレンド条件を満たす銘柄を格納するリスト
        strong_buying_tickers = []
        
        # 各候補銘柄について、条件1をチェック（前日との比較）
        for ticker in potential_tickers:
            try:
                # 個別銘柄のシグナルファイルを読み込む
                ticker_signal_file = os.path.join(input_dir, f"{ticker}_signal.csv")
                
                logger.info(f"銘柄 {ticker} の詳細シグナルファイルをチェック: {ticker_signal_file}")
                
                # ファイルが存在しない場合はスキップ
                if not os.path.exists(ticker_signal_file):
                    logger.warning(f"銘柄 {ticker} のシグナルファイルが見つかりません")
                
                # シグナルファイルを読み込み
                ticker_df = pd.read_csv(ticker_signal_file, index_col=0, parse_dates=True)
                
                # データが2行以上あることを確認（前日データが必要）
                if len(ticker_df) < 2:
                    logger.warning(f"銘柄 {ticker} のデータが不足しています (行数: {len(ticker_df)})")
                    continue
                
                # 最新2日分のデータを取得
                recent_data = ticker_df.tail(2)
                
                # 前日と当日の短期MA-中期MA差分を計算
                previous_diff = recent_data.iloc[0][short_ma] - recent_data.iloc[0][mid_ma]
                current_diff = recent_data.iloc[1][short_ma] - recent_data.iloc[1][mid_ma]
                
                # 条件1の判定結果をログ出力
                logger.info(f"銘柄 {ticker} の条件1判定:")
                logger.info(f"  前日差分: {previous_diff}")
                logger.info(f"  当日差分: {current_diff}")
                logger.info(f"  差分増加: {current_diff > previous_diff}")
                
                # 条件1: 当日の差分が前日の差分よりも大きい
                if current_diff > previous_diff:
                    # 該当銘柄をリストに追加
                    current_row = df[df['Ticker'] == ticker].iloc[0]
                    strong_buying_tickers.append({
                        'Ticker': ticker,
                        'Company': current_row['Company'],
                        '終値（最新）': current_row['Close'],
                        short_ma: current_row[short_ma],
                        mid_ma: current_row[mid_ma],
                        long_ma: current_row[long_ma],
                        '移動平均差分（前営業日）': previous_diff,
                        '移動平均差分（最新）': current_diff,
                        '移動平均差分の変化量': current_diff - previous_diff
                    })
                    logger.info(f"銘柄 {ticker} はすべての条件を満たしています！")
                else:
                    logger.info(f"銘柄 {ticker} は条件1を満たしていません")
            except Exception as e:
                logger.error(f"銘柄 {ticker} の処理中にエラーが発生しました: {str(e)}")
                # エラーのトレースバックを出力（デバッグ用）
                import traceback
                logger.error(traceback.format_exc())
        
        # 強気トレンド銘柄をデータフレームに変換
        if strong_buying_tickers:
            strong_buying_df = pd.DataFrame(strong_buying_tickers)
            
            # MA差分の変化率順にソート（変化が大きい順）
            strong_buying_df = strong_buying_df.sort_values(by='移動平均差分の変化量', ascending=False)
            
            # CSVファイルに出力
            output_file = os.path.join(output_dir, "strong_buying_trend.csv")
            strong_buying_df.to_csv(output_file, index=False)
            
            logger.info(f"強気トレンド銘柄: {len(strong_buying_df)}件を {output_file} に出力しました")
        else:
            logger.info("条件を満たす強気トレンド銘柄は見つかりませんでした")
            
            # 空のデータフレームを作成して出力
            empty_df = pd.DataFrame(columns=['Ticker', 'Company', '終値（最新）', short_ma, mid_ma, long_ma, 
                                             '移動平均差分（前営業日）', '移動平均差分（最新）', '移動平均差分の変化量'])
            output_file = os.path.join(output_dir, "strong_buying_trend.csv")
            empty_df.to_csv(output_file, index=False)
            logger.info(f"空の強気トレンドファイルを {output_file} に出力しました")
        
        return True
        
    except Exception as e:
        logger.error(f"強気トレンド銘柄抽出処理中にエラーが発生しました: {str(e)}")
        # エラーのトレースバックを出力（デバッグ用）
        import traceback
        logger.error(traceback.format_exc())
        return False

def extract_strong_selling_trend(is_test_mode: bool = False) -> bool:
    """
    latest_signal.csvから強気売りトレンドの銘柄を抽出してCSVファイルに出力します
    
    以下の条件をすべて満たす銘柄を抽出します：
    1. 前の営業日の短期移動平均と中期移動平均の差分よりも、最新の短期移動平均と中期移動平均の差分の方が小さい
    2. 「短期移動平均 ＜ 中期移動平均 ＜ 長期移動平均」の関係が成立している
    3. 最新のClose値が短期移動平均よりも低い
    
    Args:
        is_test_mode (bool): テストモードの場合はTrue、通常モードの場合はFalse
        
    Returns:
        bool: 処理が成功した場合はTrue、エラーが発生した場合はFalse
    """
    import config  # 設定値モジュールをインポート
    
    # StockSignal名前付きロガーを取得
    logger = logging.getLogger("StockSignal")
    logger.info("強気売りトレンド銘柄の抽出を開始します")
    
    try:
        # 入力ファイルのパスを設定
        if is_test_mode:
            input_dir = os.path.join(config.TEST_DIR, "StockSignal", "TechnicalSignal")
        else:
            input_dir = os.path.join(config.BASE_DIR, "StockSignal", "TechnicalSignal")
        
        input_file = os.path.join(input_dir, config.LATEST_SIGNAL_FILE)
        
        # 出力ディレクトリの設定
        if is_test_mode:
            output_dir = os.path.join(config.TEST_DIR, "Result")
        else:
            output_dir = os.path.join(config.BASE_DIR, "StockSignal", "Result")
        
        # 出力ディレクトリが存在しない場合は作成
        os.makedirs(output_dir, exist_ok=True)
        
        # 入力ファイルの存在確認
        if not os.path.exists(input_file):
            logger.error(f"ファイルが見つかりません: {input_file}")
            return False
        
        # CSVの読み込み
        logger.info(f"{input_file} を読み込みます")
        df = pd.read_csv(input_file, index_col=0, parse_dates=True)
        
        # 各銘柄の短期・中期・長期の移動平均を取得
        # 設定ファイルから移動平均期間を取得 (MA_PERIODS = [5, 25, 75])
        short_ma = f'MA{config.MA_PERIODS[0]}'  # 短期移動平均 (MA5)
        mid_ma = f'MA{config.MA_PERIODS[1]}'    # 中期移動平均 (MA25)
        long_ma = f'MA{config.MA_PERIODS[2]}'   # 長期移動平均 (MA75)
        
        # 必要なカラムの存在確認
        required_columns = ['Ticker', 'Company', 'Close', short_ma, mid_ma, long_ma]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"必要なカラムがCSVファイルに見つかりません: {missing_columns}")
            return False
        
        logger.info("各銘柄の条件判定を開始します")
        
        # 全銘柄のティッカーリストを取得
        all_tickers = df['Ticker'].unique()
        logger.info(f"処理対象の全銘柄数: {len(all_tickers)}")
        
        # 条件2: 短期MA < 中期MA < 長期MA の判定結果（買いの条件を反転）
        condition2 = (df[short_ma] < df[mid_ma]) & (df[mid_ma] < df[long_ma])
        
        # 条件3: 最新のClose値が短期移動平均よりも低い の判定結果（買いの条件を反転）
        condition3 = df['Close'] < df[short_ma]
        
        # 各銘柄の条件2と3の組み合わせ結果
        condition_results = condition2 & condition3
        
        # 条件2と3を満たす候補銘柄を抽出
        potential_tickers = df[condition_results]['Ticker'].unique()
        
        logger.info(f"条件2と3を満たす売りトレンド候補銘柄: {len(potential_tickers)}社を検出しました")
        if len(potential_tickers) > 0:
            logger.info(f"候補銘柄: {potential_tickers}")
        
        # 強気売りトレンド条件を満たす銘柄を格納するリスト
        strong_selling_tickers = []
        
        # 各候補銘柄について、条件1をチェック（前日との比較）
        for ticker in potential_tickers:
            try:
                # 個別銘柄のシグナルファイルを読み込む
                ticker_signal_file = os.path.join(input_dir, f"{ticker}_signal.csv")
                
                logger.info(f"銘柄 {ticker} の詳細シグナルファイルをチェック: {ticker_signal_file}")
                
                # ファイルが存在しない場合はスキップ
                if not os.path.exists(ticker_signal_file):
                    logger.warning(f"銘柄 {ticker} のシグナルファイルが見つかりません")
                    continue
                
                # シグナルファイルを読み込み
                ticker_df = pd.read_csv(ticker_signal_file, index_col=0, parse_dates=True)
                
                # データが2行以上あることを確認（前日データが必要）
                if len(ticker_df) < 2:
                    logger.warning(f"銘柄 {ticker} のデータが不足しています (行数: {len(ticker_df)})")
                    continue
                
                # 最新2日分のデータを取得
                recent_data = ticker_df.tail(2)
                
                # 前日と当日の短期MA-中期MA差分を計算
                # 売りトレンドでは差分がマイナスになるため、中期MA-短期MAで計算
                previous_diff = recent_data.iloc[0][mid_ma] - recent_data.iloc[0][short_ma]
                current_diff = recent_data.iloc[1][mid_ma] - recent_data.iloc[1][short_ma]
                
                # 条件1の判定結果をログ出力（売りトレンドでは差分が拡大=より大きくなる）
                logger.info(f"銘柄 {ticker} の条件1判定:")
                logger.info(f"  前日差分: {previous_diff}")
                logger.info(f"  当日差分: {current_diff}")
                logger.info(f"  差分拡大: {current_diff > previous_diff}")
                
                # 条件1: 当日の差分が前日の差分よりも大きい（売りトレンドでは差分拡大）
                if current_diff > previous_diff:
                    # 該当銘柄をリストに追加
                    current_row = df[df['Ticker'] == ticker].iloc[0]
                    strong_selling_tickers.append({
                        'Ticker': ticker,
                        'Company': current_row['Company'],
                        '終値（最新）': current_row['Close'],
                        short_ma: current_row[short_ma],
                        mid_ma: current_row[mid_ma],
                        long_ma: current_row[long_ma],
                        '移動平均差分（前営業日）': previous_diff,
                        '移動平均差分（最新）': current_diff,
                        '移動平均差分の変化量': current_diff - previous_diff
                    })
                    logger.info(f"銘柄 {ticker} はすべての売りトレンド条件を満たしています！")
                else:
                    logger.info(f"銘柄 {ticker} は条件1を満たしていません")
            except Exception as e:
                logger.error(f"銘柄 {ticker} の処理中にエラーが発生しました: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
        
        # 強気売りトレンド銘柄をデータフレームに変換
        if strong_selling_tickers:
            strong_selling_df = pd.DataFrame(strong_selling_tickers)
            
            # MA差分の変化率順にソート（変化が大きい順）
            strong_selling_df = strong_selling_df.sort_values(by='移動平均差分の変化量', ascending=False)
            
            # CSVファイルに出力
            output_file = os.path.join(output_dir, "strong_selling_trend.csv")
            strong_selling_df.to_csv(output_file, index=False)
            
            logger.info(f"強気売りトレンド銘柄: {len(strong_selling_df)}件を {output_file} に出力しました")
        else:
            logger.info("条件を満たす強気売りトレンド銘柄は見つかりませんでした")
            
            # 空のデータフレームを作成して出力
            empty_df = pd.DataFrame(columns=['Ticker', 'Company', '終値（最新）', short_ma, mid_ma, long_ma, 
                                             '移動平均差分（前営業日）', '移動平均差分（最新）', '移動平均差分の変化量'])
            output_file = os.path.join(output_dir, "strong_selling_trend.csv")
            empty_df.to_csv(output_file, index=False)
            logger.info(f"空の強気売りトレンドファイルを {output_file} に出力しました")
        
        return True
        
    except Exception as e:
        logger.error(f"強気売りトレンド銘柄抽出処理中にエラーが発生しました: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
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