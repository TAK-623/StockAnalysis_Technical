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
    MACD-RSI、MACD-RCI、BB-MACDの各シグナルを抽出します。
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
            input_dir = os.path.join(config.TEST_DIR, "StockSignal", "TechnicalSignal")
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
        required_columns = ['Ticker', 'Company', 'Theme', 'MACD-RSI', 'MACD-RCI', 'BB-MACD', 'Close', 'High', 'Low', 'MACD', 'BB_Middle', rsi_long_col, rci_long_col]
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
        # 3. 必要なカラム（銘柄コード、会社名、テーマ、終値、MACD、RSI長期）のみを選択
        macd_rsi_buy_signals = df[(df['MACD-RSI'] == 'Buy') & (df['Close'] > df['Midpoint'])]
        macd_rsi_buy_signals = macd_rsi_buy_signals[['Ticker', 'Company', 'Theme', 'Close', 'MACD', rsi_long_col]]
        
        # 数値データの小数点以下桁数を調整（小数点以下2桁に丸める）
        macd_rsi_buy_signals['MACD'] = macd_rsi_buy_signals['MACD'].round(2)
        macd_rsi_buy_signals[rsi_long_col] = macd_rsi_buy_signals[rsi_long_col].round(2)
        
        # 終値の表示形式を調整（小数点以下が0の場合は整数表示、それ以外は小数点以下1桁）
        macd_rsi_buy_signals['Close'] = macd_rsi_buy_signals['Close'].apply(
            lambda x: int(x) if x == int(x) else round(x, 1)
        )
        
        # カラム名を日本語に変更（レポートの可読性向上のため）
        macd_rsi_buy_signals = macd_rsi_buy_signals.rename(columns={
            'Theme': 'テーマ',
            'Close': '終値',
            'MACD': 'MACD',
            rsi_long_col: f'RSI{config.RSI_LONG_PERIOD}'
        })
        # 買いシグナル出力ファイルのパスを設定
        macd_rsi_buy_output_file = os.path.join(output_dir, "macd_rsi_signal_result_buy.csv")
        
        # Sellシグナルの抽出処理
        # 1. MACD-RSIカラムが'Sell'のレコードのみを抽出
        # 2. 追加条件：終値が高値と安値の中間よりも下にある（下髭が短い銘柄）
        # 3. 必要なカラム（銘柄コード、会社名、テーマ、終値、MACD、RSI長期）のみを選択
        macd_rsi_sell_signals = df[(df['MACD-RSI'] == 'Sell') & (df['Close'] < df['Midpoint'])]
        macd_rsi_sell_signals = macd_rsi_sell_signals[['Ticker', 'Company', 'Theme', 'Close', 'MACD', rsi_long_col]]
        
        # 数値データの小数点以下桁数を調整
        macd_rsi_sell_signals['MACD'] = macd_rsi_sell_signals['MACD'].round(2)
        macd_rsi_sell_signals[rsi_long_col] = macd_rsi_sell_signals[rsi_long_col].round(2)
        
        # 終値の表示形式を調整（小数点以下が0の場合は整数表示、それ以外は小数点以下1桁）
        macd_rsi_sell_signals['Close'] = macd_rsi_sell_signals['Close'].apply(
            lambda x: int(x) if x == int(x) else round(x, 1)
        )
        
        # カラム名を日本語に変更（レポートの可読性向上のため）
        macd_rsi_sell_signals = macd_rsi_sell_signals.rename(columns={
            'Theme': 'テーマ',
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
        # 3. 必要なカラム（銘柄コード、会社名、テーマ、終値、MACD、RCI短期、RCI長期）のみを選択
        macd_rci_buy_signals = df[(df['MACD-RCI'] == 'Buy') & (df['Close'] > df['Midpoint'])]
        macd_rci_buy_signals = macd_rci_buy_signals[['Ticker', 'Company', 'Theme', 'Close', 'MACD', rci_short_col, rci_long_col]]
        
        # 数値データの小数点以下桁数を調整（小数点以下2桁に丸める）
        macd_rci_buy_signals['MACD'] = macd_rci_buy_signals['MACD'].round(2)
        macd_rci_buy_signals[rci_short_col] = macd_rci_buy_signals[rci_short_col].round(2)
        macd_rci_buy_signals[rci_long_col] = macd_rci_buy_signals[rci_long_col].round(2)
        
        # 終値の表示形式を調整（小数点以下が0の場合は整数表示、それ以外は小数点以下1桁）
        macd_rci_buy_signals['Close'] = macd_rci_buy_signals['Close'].apply(
            lambda x: int(x) if x == int(x) else round(x, 1)
        )
        
        # カラム名を日本語に変更（レポートの可読性向上のため）
        macd_rci_buy_signals = macd_rci_buy_signals.rename(columns={
            'Theme': 'テーマ',
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
        # 3. 必要なカラム（銘柄コード、会社名、テーマ、終値、MACD、RCI短期、RCI長期）のみを選択
        macd_rci_sell_signals = df[(df['MACD-RCI'] == 'Sell') & (df['Close'] < df['Midpoint'])]
        macd_rci_sell_signals = macd_rci_sell_signals[['Ticker', 'Company', 'Theme', 'Close', 'MACD', rci_short_col, rci_long_col]]
        
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
            'Theme': 'テーマ',
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
        
        # === BB-MACD シグナル処理 ===
        # Buyシグナルの抽出処理
        # 1. BB-MACDカラムが'Buy'のレコードのみを抽出
        # 2. 追加条件：終値が高値と安値の中間よりも上にある（上髭が短い銘柄）
        # 3. 必要なカラム（銘柄コード、会社名、テーマ、終値、MACD、BB_Middle）のみを選択
        bb_macd_buy_signals = df[(df['BB-MACD'] == 'Buy') & (df['Close'] > df['Midpoint'])]
        bb_macd_buy_signals = bb_macd_buy_signals[['Ticker', 'Company', 'Theme', 'Close', 'MACD', 'BB_Middle']]
        
        # 数値データの小数点以下桁数を調整（小数点以下2桁に丸める）
        bb_macd_buy_signals['MACD'] = bb_macd_buy_signals['MACD'].round(2)
        bb_macd_buy_signals['BB_Middle'] = bb_macd_buy_signals['BB_Middle'].round(2)
        
        # 終値の表示形式を調整（小数点以下が0の場合は整数表示、それ以外は小数点以下1桁）
        bb_macd_buy_signals['Close'] = bb_macd_buy_signals['Close'].apply(
            lambda x: int(x) if x == int(x) else round(x, 1)
        )
        
        # カラム名を日本語に変更（レポートの可読性向上のため）
        bb_macd_buy_signals = bb_macd_buy_signals.rename(columns={
            'Theme': 'テーマ',
            'Close': '終値',
            'MACD': 'MACD',
            'BB_Middle': '20SMA'
        })
        
        # 買いシグナル出力ファイルのパスを設定
        bb_macd_buy_output_file = os.path.join(output_dir, "macd_bb_signal_result_buy.csv")
        
        # Sellシグナルの抽出処理
        # 1. BB-MACDカラムが'Sell'のレコードのみを抽出
        # 2. 追加条件：終値が高値と安値の中間よりも下にある（下髭が短い銘柄）
        # 3. 必要なカラム（銘柄コード、会社名、テーマ、終値、MACD、BB_Middle）のみを選択
        bb_macd_sell_signals = df[(df['BB-MACD'] == 'Sell') & (df['Close'] < df['Midpoint'])]
        bb_macd_sell_signals = bb_macd_sell_signals[['Ticker', 'Company', 'Theme', 'Close', 'MACD', 'BB_Middle']]
        
        # 数値データの小数点以下桁数を調整
        bb_macd_sell_signals['MACD'] = bb_macd_sell_signals['MACD'].round(2)
        bb_macd_sell_signals['BB_Middle'] = bb_macd_sell_signals['BB_Middle'].round(2)
        
        # 終値の表示形式を調整（小数点以下が0の場合は整数表示、それ以外は小数点以下1桁）
        bb_macd_sell_signals['Close'] = bb_macd_sell_signals['Close'].apply(
            lambda x: int(x) if x == int(x) else round(x, 1)
        )
        
        # カラム名を日本語に変更（レポートの可読性向上のため）
        bb_macd_sell_signals = bb_macd_sell_signals.rename(columns={
            'Theme': 'テーマ',
            'Close': '終値',
            'MACD': 'MACD',
            'BB_Middle': '20SMA'
        })
        
        # 売りシグナル出力ファイルのパスを設定
        bb_macd_sell_output_file = os.path.join(output_dir, "macd_bb_signal_result_sell.csv")
        
        # 結果をCSVファイルに出力
        # index=False: インデックスは出力しない（必要な情報のみをクリーンに出力）
        bb_macd_buy_signals.to_csv(bb_macd_buy_output_file, index=False)
        bb_macd_sell_signals.to_csv(bb_macd_sell_output_file, index=False)
        
        # 処理結果のログ出力
        # 何件のシグナルが検出され、どのファイルに出力されたかを記録
        logger.info(f"BB-MACD Buyシグナル（Close > Midpoint条件付き）: {len(bb_macd_buy_signals)}件を {bb_macd_buy_output_file} に出力しました")
        logger.info(f"BB-MACD Sellシグナル（Close < Midpoint条件付き）: {len(bb_macd_sell_signals)}件を {bb_macd_sell_output_file} に出力しました")
        
        # === 両シグナル一致（MACD-RSIとMACD-RCIが両方とも同じシグナル）を抽出 ===
        # 両方がBuyの銘柄を抽出
        # 追加条件：終値が高値と安値の中間よりも上にある（上髭が短い銘柄）
        macd_rsi_rci_buy_signals = df[(df['MACD-RSI'] == 'Buy') & 
                                      (df['MACD-RCI'] == 'Buy') & 
                                      (df['Close'] > df['Midpoint'])]
        
        # 必要なカラムのみを選択（両方のシグナルに使用されている指標を含める）
        both_buy_columns = ['Ticker', 'Company', 'Theme', 'Close', 'MACD', rsi_long_col, rci_short_col, rci_long_col]
        macd_rsi_rci_buy_signals = macd_rsi_rci_buy_signals[both_buy_columns]
        
        # 数値データの小数点以下桁数を調整
        macd_rsi_rci_buy_signals['MACD'] = macd_rsi_rci_buy_signals['MACD'].round(2)
        macd_rsi_rci_buy_signals[rsi_long_col] = macd_rsi_rci_buy_signals[rsi_long_col].round(2)
        macd_rsi_rci_buy_signals[rci_short_col] = macd_rsi_rci_buy_signals[rci_short_col].round(2)
        macd_rsi_rci_buy_signals[rci_long_col] = macd_rsi_rci_buy_signals[rci_long_col].round(2)
        
        # 終値の表示形式を調整（小数点以下が0の場合は整数表示、それ以外は小数点以下1桁）
        macd_rsi_rci_buy_signals['Close'] = macd_rsi_rci_buy_signals['Close'].apply(
            lambda x: int(x) if x == int(x) else round(x, 1)
        )
        
        # カラム名を日本語に変更
        macd_rsi_rci_buy_signals = macd_rsi_rci_buy_signals.rename(columns={
            'Theme': 'テーマ',
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
        both_sell_columns = ['Ticker', 'Company', 'Theme', 'Close', 'MACD', rsi_long_col, rci_short_col, rci_long_col]
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
            'Theme': 'テーマ',
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

def extract_push_mark_signals(is_test_mode: bool = False) -> bool:
    """
    latest_signal.csvから押し目の銘柄を抽出してCSVファイルに出力します
    
    以下の条件をすべて満たす銘柄を抽出します：
    1. "短期移動平均-中期移動平均"の絶対値がその銘柄の最新Close値の2%以下
    2. 前日の短期移動平均ー中期移動平均よりも最新の短期移動平均ー中期移動平均が大きい
    3. 中期の移動平均線が上向きであること（前日の中期MA < 当日の中期MA）
    
    Args:
        is_test_mode (bool): テストモードの場合はTrue、通常モードの場合はFalse
        
    Returns:
        bool: 処理が成功した場合はTrue、エラーが発生した場合はFalse
    """
    import config  # 設定値モジュールをインポート
    
    # StockSignal名前付きロガーを取得
    logger = logging.getLogger("StockSignal")
    logger.info("押し目銘柄の抽出を開始します")
    logger.info("抽出条件:")
    logger.info("1. 「短期移動平均-中期移動平均」の絶対値がその銘柄の最新Close値の2%以下")
    logger.info("2. 前日の短期移動平均ー中期移動平均よりも最新の短期移動平均ー中期移動平均が大きい")
    logger.info("3. 中期の移動平均線が上向きであること（前日の中期MA < 当日の中期MA）")
    
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
        
        # 各銘柄の短期・中期の移動平均を取得
        # 設定ファイルから移動平均期間を取得 (MA_PERIODS = [5, 25, 75])
        short_ma = f'MA{config.MA_PERIODS[0]}'  # 短期移動平均 (MA5)
        mid_ma = f'MA{config.MA_PERIODS[1]}'    # 中期移動平均 (MA25)
        
        # 必要なカラムの存在確認
        required_columns = ['Ticker', 'Company', 'Theme', 'Close', short_ma, mid_ma]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"必要なカラムがCSVファイルに見つかりません: {missing_columns}")
            return False

        logger.info("各銘柄の条件判定を開始します")

        # 全銘柄のティッカーリストを取得
        all_tickers = df['Ticker'].unique()
        logger.info(f"処理対象の全銘柄数: {len(all_tickers)}")

        # 条件1: "短期移動平均-中期移動平均"の絶対値がその銘柄の最新Close値の2%以下
        df['MA_Diff'] = df[short_ma] - df[mid_ma]
        df['MA_Diff_Abs'] = abs(df['MA_Diff'])
        df['Close_2_Percent'] = df['Close'] * 0.02
        condition1 = df['MA_Diff_Abs'] <= df['Close_2_Percent']

        # 条件1を満たす候補銘柄を抽出
        potential_tickers = df[condition1]['Ticker'].unique()

        logger.info(f"条件1を満たす候補銘柄: {len(potential_tickers)}社を検出しました")
        if len(potential_tickers) > 0:
            logger.info(f"候補銘柄: {potential_tickers}")
        
        # 押し目条件を満たす銘柄を格納するリスト
        push_mark_tickers = []
        
        # 各候補銘柄について、条件2をチェック（前日との比較）
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
                previous_diff = recent_data.iloc[0][short_ma] - recent_data.iloc[0][mid_ma]
                current_diff = recent_data.iloc[1][short_ma] - recent_data.iloc[1][mid_ma]
                
                # 前日と当日の中期移動平均を取得
                previous_mid_ma = recent_data.iloc[0][mid_ma]
                current_mid_ma = recent_data.iloc[1][mid_ma]
                
                # 条件2の判定結果をログ出力
                logger.info(f"銘柄 {ticker} の条件2判定:")
                logger.info(f"  前日差分: {previous_diff:.4f}")
                logger.info(f"  当日差分: {current_diff:.4f}")
                logger.info(f"  差分増加: {current_diff > previous_diff}")
                
                # 条件3の判定結果をログ出力
                logger.info(f"銘柄 {ticker} の条件3判定:")
                logger.info(f"  前日中期MA: {previous_mid_ma:.4f}")
                logger.info(f"  当日中期MA: {current_mid_ma:.4f}")
                logger.info(f"  中期MA上向き: {current_mid_ma > previous_mid_ma}")
                
                # 条件2: 当日の差分が前日の差分よりも大きい
                # 条件3: 中期移動平均が上向き（前日 < 当日）
                if current_diff > previous_diff and current_mid_ma > previous_mid_ma:
                    # 該当銘柄をリストに追加
                    current_row = df[df['Ticker'] == ticker].iloc[0]
                    push_mark_tickers.append({
                        'Ticker': ticker,
                        '銘柄名': current_row['Company'],
                        'テーマ': current_row['Theme'],
                        '最新の終値': current_row['Close'],
                        '短期移動平均': current_row[short_ma],
                        '中期移動平均': current_row[mid_ma]
                    })
                    logger.info(f"銘柄 {ticker} はすべての押し目条件を満たしています！")
                else:
                    if current_diff <= previous_diff:
                        logger.info(f"銘柄 {ticker} は条件2を満たしていません（差分増加なし）")
                    if current_mid_ma <= previous_mid_ma:
                        logger.info(f"銘柄 {ticker} は条件3を満たしていません（中期MA上向きでない）")
            except Exception as e:
                logger.error(f"銘柄 {ticker} の処理中にエラーが発生しました: {str(e)}")
                # エラーのトレースバックを出力（デバッグ用）
                import traceback
                logger.error(traceback.format_exc())
        
        # 押し目銘柄をデータフレームに変換
        if push_mark_tickers:
            push_mark_df = pd.DataFrame(push_mark_tickers)
            
            # 数値データの小数点以下桁数を調整
            push_mark_df['短期移動平均'] = push_mark_df['短期移動平均'].round(2)
            push_mark_df['中期移動平均'] = push_mark_df['中期移動平均'].round(2)
            
            # 終値の表示形式を調整（小数点以下が0の場合は整数表示、それ以外は小数点以下1桁）
            push_mark_df['最新の終値'] = push_mark_df['最新の終値'].apply(
                lambda x: int(x) if x == int(x) else round(x, 1)
            )
            
            # CSVファイルに出力（インデックスなし）
            output_file = os.path.join(output_dir, "push_mark.csv")
            push_mark_df.to_csv(output_file, index=False, encoding='utf-8-sig')
            
            logger.info(f"押し目銘柄: {len(push_mark_df)}件を {output_file} に出力しました")
            
            # 結果の詳細をログに出力（最初の5社まで）
            logger.info("押し目銘柄（上位5社）:")
            for i, stock in enumerate(push_mark_tickers[:5]):
                logger.info(f"  {i+1}. {stock['Ticker']} {stock['銘柄名']} ({stock['テーマ']}) "
                           f"終値: {stock['最新の終値']}, "
                           f"短期MA: {stock['短期移動平均']:.2f}, "
                           f"中期MA: {stock['中期移動平均']:.2f}")
        else:
            logger.info("条件を満たす押し目銘柄は見つかりませんでした")
            
            # 空のデータフレームを作成して出力
            empty_df = pd.DataFrame(columns=[
                'Ticker', '銘柄名', 'テーマ', '最新の終値', '短期移動平均', '中期移動平均'
            ])
            output_file = os.path.join(output_dir, "push_mark.csv")
            empty_df.to_csv(output_file, index=False, encoding='utf-8-sig')
            logger.info(f"空の押し目ファイルを {output_file} に出力しました")
        
        return True
        
    except Exception as e:
        logger.error(f"押し目銘柄抽出処理中にエラーが発生しました: {str(e)}")
        # エラーのトレースバックを出力（デバッグ用）
        import traceback
        logger.error(traceback.format_exc())
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
        required_columns = ['Ticker', 'Company', 'Theme', 'Close', 'Volume', short_ma, mid_ma, long_ma]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"必要なカラムがCSVファイルに見つかりません: {missing_columns}")
            return False

        logger.info("各銘柄の条件判定を開始します")

        # 全銘柄のティッカーリストを取得
        all_tickers = df['Ticker'].unique()
        logger.info(f"処理対象の全銘柄数: {len(all_tickers)}")

        # 条件2: 短期MA > 中期MA > 長期MA の判定結果
        condition2 = (df[short_ma] > df[mid_ma]) & (df[mid_ma] > df[long_ma])

        # 条件3: 最新のClose値が短期移動平均よりも高い の判定結果
        condition3 = df['Close'] > df[short_ma]

        # 条件4: 出来高が10万以上
        condition4 = df['Volume'] >= 100000

        # 各銘柄の条件2、3、4の組み合わせ結果
        condition_results = condition2 & condition3 & condition4

        # 条件を満たす候補銘柄を抽出
        potential_tickers = df[condition_results]['Ticker'].unique()

        logger.info(f"条件2,3,4を満たす候補銘柄: {len(potential_tickers)}社を検出しました")
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
                    ma_diff_ratio = current_diff / current_row['Close'] * 100
                    strong_buying_tickers.append({
                        'Ticker': ticker,
                        'Company': current_row['Company'],
                        'Theme': current_row['Theme'],
                        '終値（最新）': current_row['Close'],
                        'Volume': current_row['Volume'],
                        short_ma: current_row[short_ma],
                        mid_ma: current_row[mid_ma],
                        'MA_Diff_Previous': previous_diff,
                        'MA_Diff_Current': current_diff,
                        'MA_Diff_Change': current_diff - previous_diff,
                        'MA_Diff_Ratio': ma_diff_ratio
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
            
            # 列名を日本語に変更（より簡潔なラベルに）
            strong_buying_df = strong_buying_df.rename(columns={
                'Theme': 'テーマ',  # テーマ列を日本語に変更
                'Close': '終値（最新）',
                'Volume': '出来高',
                'MA_Diff_Previous': '移動平均差分（前営業日）',
                'MA_Diff_Current': '移動平均差分（最新）',
                'MA_Diff_Change': '変化量',
                'MA_Diff_Ratio': '変化率'
            })
            
            # MA差分の株価に対する割合でソート（比率が大きい順）
            strong_buying_df = strong_buying_df.sort_values(by='変化率', ascending=False)
            
            # 列の順序を変更（long_maを含めない）
            columns_order = [
                'Ticker', 'Company', 'テーマ', '終値（最新）', '変化率', 
                '変化量', '移動平均差分（最新）', '移動平均差分（前営業日）',
                short_ma, mid_ma, '出来高'
            ]
            strong_buying_df = strong_buying_df[columns_order]
            
            # CSVファイルに出力
            output_file = os.path.join(output_dir, "strong_buying_trend.csv")
            strong_buying_df.to_csv(output_file, index=False)
            
            logger.info(f"強気トレンド銘柄: {len(strong_buying_df)}件を {output_file} に出力しました")
        else:
            logger.info("条件を満たす強気トレンド銘柄は見つかりませんでした")
            
            # 空のデータフレームを作成して出力
            empty_df = pd.DataFrame(columns=[
                'Ticker', 'Company', 'テーマ', '終値（最新）', '変化率',
                '変化量', '移動平均差分（最新）', '移動平均差分（前営業日）',
                short_ma, mid_ma, '出来高'
            ])
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
        required_columns = ['Ticker', 'Company', 'Theme', 'Close', 'Volume', short_ma, mid_ma, long_ma]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"必要なカラムがCSVファイルに見つかりません: {missing_columns}")
            return False

        logger.info("各銘柄の条件判定を開始します")

        # 全銘柄のティッカーリストを取得
        all_tickers = df['Ticker'].unique()
        logger.info(f"処理対象の全銘柄数: {len(all_tickers)}")

        # 条件2: 短期MA < 中期MA < 長期MA の判定結果
        condition2 = (df[short_ma] < df[mid_ma]) & (df[mid_ma] < df[long_ma])

        # 条件3: 最新のClose値が短期移動平均よりも低い の判定結果
        condition3 = df['Close'] < df[short_ma]

        # 条件4: 出来高が10万以上
        condition4 = df['Volume'] >= 100000

        # 各銘柄の条件2、3、4の組み合わせ結果
        condition_results = condition2 & condition3 & condition4

        # 条件を満たす候補銘柄を抽出
        potential_tickers = df[condition_results]['Ticker'].unique()

        logger.info(f"条件2,3,4を満たす売りトレンド候補銘柄: {len(potential_tickers)}社を検出しました")
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
                    ma_diff_ratio = current_diff / current_row['Close'] * 100
                    strong_selling_tickers.append({
                        'Ticker': ticker,
                        'Company': current_row['Company'],
                        'Theme': current_row['Theme'],
                        '終値（最新）': current_row['Close'],
                        'Volume': current_row['Volume'],
                        short_ma: current_row[short_ma],
                        mid_ma: current_row[mid_ma],
                        'MA_Diff_Previous': previous_diff,
                        'MA_Diff_Current': current_diff,
                        'MA_Diff_Change': current_diff - previous_diff,
                        'MA_Diff_Ratio': ma_diff_ratio
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
            
            # 列名を日本語に変更（より簡潔なラベルに）
            strong_selling_df = strong_selling_df.rename(columns={
                'Theme': 'テーマ',  # テーマ列を日本語に変更
                'Close': '終値（最新）',
                'Volume': '出来高',
                'MA_Diff_Previous': '移動平均差分（前営業日）',
                'MA_Diff_Current': '移動平均差分（最新）',
                'MA_Diff_Change': '変化量',
                'MA_Diff_Ratio': '変化率'
            })
            
            # MA差分の株価に対する割合でソート（比率が大きい順）
            strong_selling_df = strong_selling_df.sort_values(by='変化率', ascending=False)
            
            # 列の順序を変更（long_maを含めない）
            columns_order = [
                'Ticker', 'Company', 'テーマ', '終値（最新）', '変化率', 
                '変化量', '移動平均差分（最新）', '移動平均差分（前営業日）',
                short_ma, mid_ma, '出来高'
            ]
            strong_selling_df = strong_selling_df[columns_order]
            
            # CSVファイルに出力
            output_file = os.path.join(output_dir, "strong_selling_trend.csv")
            strong_selling_df.to_csv(output_file, index=False)
            
            logger.info(f"強気売りトレンド銘柄: {len(strong_selling_df)}件を {output_file} に出力しました")
        else:
            logger.info("条件を満たす強気売りトレンド銘柄は見つかりませんでした")
            
            # 空のデータフレームを作成して出力
            empty_df = pd.DataFrame(columns=[
                'Ticker', 'Company', 'テーマ', '終値（最新）', '変化率',
                '変化量', '移動平均差分（最新）', '移動平均差分（前営業日）',
                short_ma, mid_ma, '出来高'
            ])
            output_file = os.path.join(output_dir, "strong_selling_trend.csv")
            empty_df.to_csv(output_file, index=False)
            logger.info(f"空の強気売りトレンドファイルを {output_file} に出力しました")
        
        return True
        
    except Exception as e:
        logger.error(f"強気売りトレンド銘柄抽出処理中にエラーが発生しました: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def extract_sanyaku_signals(is_test_mode: bool = False) -> bool:
    """
    latest_signal.csvから三役好転・三役暗転の銘柄を抽出してCSVファイルに出力します
    
    Args:
        is_test_mode (bool): テストモードの場合はTrue、通常モードの場合はFalse
        
    Returns:
        bool: 処理が成功した場合はTrue、エラーが発生した場合はFalse
    """
    import config  # 設定値モジュールをインポート
    
    # StockSignal名前付きロガーを取得
    logger = logging.getLogger("StockSignal")
    logger.info("三役好転・三役暗転銘柄の抽出を開始します")
    logger.info("抽出条件:")
    logger.info("- 三役好転: 価格が雲の上 + 遅行線が価格より上 + 転換線が基準線より上")
    logger.info("- 三役暗転: 価格が雲の下 + 遅行線が価格より下 + 転換線が基準線より下")
    logger.info("- 雲の上にある銘柄: 抵抗線の目安＝先行スパンA・B の低い方（雲の下限）")
    logger.info("- 雲の下にある銘柄: 抵抗線の目安＝先行スパンA・B の高い方（雲の上限）")
    
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
        
        # 必要なカラムの存在確認
        required_columns = ['Ticker', 'Company', 'Theme', 'Close', 'SanYaku_Kouten', 'SanYaku_Anten', 
                           'Ichimoku_Tenkan', 'Ichimoku_Kijun', 'Ichimoku_SenkouA', 'Ichimoku_SenkouB',
                           'Ichimoku_Above_Cloud', 'Ichimoku_Below_Cloud',
                           'Ichimoku_Chikou_Above_Price', 'Ichimoku_Chikou_Below_Price']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"必要なカラムがCSVファイルに見つかりません: {missing_columns}")
            return False
        
        # === 三役好転銘柄の抽出 ===
        sanyaku_kouten_signals = df[df['SanYaku_Kouten'] == True]
        sanyaku_kouten_signals = sanyaku_kouten_signals[['Ticker', 'Company', 'Theme', 'Close', 
                                                        'Ichimoku_Tenkan', 'Ichimoku_Kijun', 
                                                        'Ichimoku_SenkouA', 'Ichimoku_SenkouB',
                                                        'Ichimoku_Above_Cloud', 'Ichimoku_Below_Cloud']].copy()
        
        # 雲の位置に基づいて抵抗線の目安を設定
        # 雲の上：先行スパンの低い方（雲の下限が抵抗線）、雲の下：先行スパンの高い方（雲の上限が抵抗線）
        sanyaku_kouten_signals['抵抗線の目安'] = sanyaku_kouten_signals.apply(
            lambda row: min(row['Ichimoku_SenkouA'], row['Ichimoku_SenkouB']) if row['Ichimoku_Above_Cloud'] 
            else max(row['Ichimoku_SenkouA'], row['Ichimoku_SenkouB']), axis=1
        )
        
        # 不要な列を削除
        sanyaku_kouten_signals = sanyaku_kouten_signals.drop(['Ichimoku_SenkouA', 'Ichimoku_SenkouB', 
                                                             'Ichimoku_Above_Cloud', 'Ichimoku_Below_Cloud'], axis=1)
        
        # 数値データの小数点以下桁数を調整
        sanyaku_kouten_signals['Ichimoku_Tenkan'] = sanyaku_kouten_signals['Ichimoku_Tenkan'].round(2)
        sanyaku_kouten_signals['Ichimoku_Kijun'] = sanyaku_kouten_signals['Ichimoku_Kijun'].round(2)
        sanyaku_kouten_signals['抵抗線の目安'] = sanyaku_kouten_signals['抵抗線の目安'].round(2)
        
        # 終値の表示形式を調整
        sanyaku_kouten_signals['Close'] = sanyaku_kouten_signals['Close'].apply(
            lambda x: int(x) if x == int(x) else round(x, 1)
        )
        
        # カラム名を日本語に変更
        sanyaku_kouten_signals = sanyaku_kouten_signals.rename(columns={
            'Theme': 'テーマ',
            'Close': '終値',
            'Ichimoku_Tenkan': '転換線',
            'Ichimoku_Kijun': '基準線'
        })
        
        # 三役好転出力ファイルのパスを設定
        sanyaku_kouten_output_file = os.path.join(output_dir, "sanyaku_kouten.csv")
        
        # === 三役暗転銘柄の抽出 ===
        sanyaku_anten_signals = df[df['SanYaku_Anten'] == True]
        sanyaku_anten_signals = sanyaku_anten_signals[['Ticker', 'Company', 'Theme', 'Close', 
                                                      'Ichimoku_Tenkan', 'Ichimoku_Kijun', 
                                                      'Ichimoku_SenkouA', 'Ichimoku_SenkouB',
                                                      'Ichimoku_Above_Cloud', 'Ichimoku_Below_Cloud']].copy()
        
        # 雲の位置に基づいて抵抗線の目安を設定
        # 雲の上：先行スパンの低い方（雲の下限が抵抗線）、雲の下：先行スパンの高い方（雲の上限が抵抗線）
        sanyaku_anten_signals['抵抗線の目安'] = sanyaku_anten_signals.apply(
            lambda row: min(row['Ichimoku_SenkouA'], row['Ichimoku_SenkouB']) if row['Ichimoku_Above_Cloud'] 
            else max(row['Ichimoku_SenkouA'], row['Ichimoku_SenkouB']), axis=1
        )
        
        # 不要な列を削除
        sanyaku_anten_signals = sanyaku_anten_signals.drop(['Ichimoku_SenkouA', 'Ichimoku_SenkouB',
                                                           'Ichimoku_Above_Cloud', 'Ichimoku_Below_Cloud'], axis=1)
        
        # 数値データの小数点以下桁数を調整
        sanyaku_anten_signals['Ichimoku_Tenkan'] = sanyaku_anten_signals['Ichimoku_Tenkan'].round(2)
        sanyaku_anten_signals['Ichimoku_Kijun'] = sanyaku_anten_signals['Ichimoku_Kijun'].round(2)
        sanyaku_anten_signals['抵抗線の目安'] = sanyaku_anten_signals['抵抗線の目安'].round(2)
        
        # 終値の表示形式を調整
        sanyaku_anten_signals['Close'] = sanyaku_anten_signals['Close'].apply(
            lambda x: int(x) if x == int(x) else round(x, 1)
        )
        
        # カラム名を日本語に変更
        sanyaku_anten_signals = sanyaku_anten_signals.rename(columns={
            'Theme': 'テーマ',
            'Close': '終値',
            'Ichimoku_Tenkan': '転換線',
            'Ichimoku_Kijun': '基準線'
        })
        
        # 三役暗転出力ファイルのパスを設定
        sanyaku_anten_output_file = os.path.join(output_dir, "sanyaku_anten.csv")
        
        # 結果をCSVファイルに出力
        if len(sanyaku_kouten_signals) > 0:
            sanyaku_kouten_signals = format_sanyaku_output(sanyaku_kouten_signals)
            sanyaku_kouten_signals.to_csv(sanyaku_kouten_output_file, index=False)
            logger.info(f"三役好転銘柄: {len(sanyaku_kouten_signals)}件を {sanyaku_kouten_output_file} に出力しました")
        else:
            create_empty_sanyaku_file(sanyaku_kouten_output_file)
            logger.info("三役好転銘柄: 0件（空ファイルを出力）")
        
        if len(sanyaku_anten_signals) > 0:
            sanyaku_anten_signals = format_sanyaku_output(sanyaku_anten_signals)
            sanyaku_anten_signals.to_csv(sanyaku_anten_output_file, index=False)
            logger.info(f"三役暗転銘柄: {len(sanyaku_anten_signals)}件を {sanyaku_anten_output_file} に出力しました")
        else:
            create_empty_sanyaku_file(sanyaku_anten_output_file)
            logger.info("三役暗転銘柄: 0件（空ファイルを出力）")
        
        return True
        
    except Exception as e:
        logger.error(f"三役好転・三役暗転銘柄抽出処理中にエラーが発生しました: {str(e)}")
        return False

def format_sanyaku_output(df: pd.DataFrame) -> pd.DataFrame:
    """
    三役好転・三役暗転出力データの書式を整える
    
    Args:
        df: 三役好転・三役暗転データのデータフレーム
        
    Returns:
        pd.DataFrame: 書式を整えたデータフレーム
    """
    # 数値データの小数点以下桁数を調整
    df['転換線'] = df['転換線'].round(2)
    df['基準線'] = df['基準線'].round(2)
    df['抵抗線の目安'] = df['抵抗線の目安'].round(2)
    
    # 終値の表示形式を調整
    df['終値'] = df['終値'].apply(
        lambda x: int(x) if x == int(x) else round(x, 1)
    )
    
    # 列の順序を調整（三役好転・暗転では前日の値は不要）
    columns_order = [
        'Ticker', 'Company', 'テーマ', '終値', '転換線', '基準線', '抵抗線の目安'
    ]
    
    return df[columns_order]

def create_empty_sanyaku_file(file_path: str):
    """
    空の三役好転・三役暗転ファイルを作成する
    
    Args:
        file_path: 作成するファイルのパス
    """
    empty_df = pd.DataFrame(columns=[
        'Ticker', 'Company', 'テーマ', '終値', '転換線', '基準線', '抵抗線の目安'
    ])
    empty_df.to_csv(file_path, index=False)

def extract_ichimoku_cross_signals(is_test_mode: bool = False) -> bool:
    """
    転換線・基準線のクロス銘柄を抽出してCSVファイルに出力します
    
    雲の上・下での転換線と基準線のゴールデンクロス・デッドクロスを検出し、
    さらに遅行線の条件も同時に満たす銘柄のみを抽出します。
    
    抽出条件：
    - ゴールデンクロス: 前営業日(転換線 <= 基準線) → 最新営業日(転換線 > 基準線) + 遅行線が価格より上
    - デッドクロス: 前営業日(転換線 >= 基準線) → 最新営業日(転換線 < 基準線) + 遅行線が価格より下
    
    Args:
        is_test_mode (bool): テストモードの場合はTrue、通常モードの場合はFalse
        
    Returns:
        bool: 処理が成功した場合はTrue、エラーが発生した場合はFalse
    """
    import config  # 設定値モジュールをインポート
    
    # StockSignal名前付きロガーを取得
    logger = logging.getLogger("StockSignal")
    logger.info("一目均衡表転換線・基準線クロス銘柄の抽出を開始します")
    logger.info("抽出条件:")
    logger.info("- ゴールデンクロス: 転換線が基準線を下から上に抜ける + 遅行線が価格より上")
    logger.info("- デッドクロス: 転換線が基準線を上から下に抜ける + 遅行線が価格より下")
    logger.info("- 雲の上にある銘柄: 抵抗線の目安＝先行スパンA・B の低い方（雲の下限）")
    logger.info("- 雲の下にある銘柄: 抵抗線の目安＝先行スパンA・B の高い方（雲の上限）")
    logger.info("- 各条件に雲の上・下の状態を組み合わせて分類")
    
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
        
        # 必要なカラムの存在確認
        required_columns = ['Ticker', 'Company', 'Theme', 'Close', 'Ichimoku_Tenkan', 'Ichimoku_Kijun', 
                           'Ichimoku_Above_Cloud', 'Ichimoku_Below_Cloud', 'Ichimoku_SenkouA', 'Ichimoku_SenkouB',
                           'Ichimoku_Chikou_Above_Price', 'Ichimoku_Chikou_Below_Price']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"必要なカラムがCSVファイルに見つかりません: {missing_columns}")
            return False
        
        # 全銘柄のティッカーリストを取得
        all_tickers = df['Ticker'].unique()
        logger.info(f"処理対象の全銘柄数: {len(all_tickers)}")
        
        # 各種クロス信号を格納するリスト
        gc_under_cloud_tickers = []    # 雲の下でのゴールデンクロス
        gc_upper_cloud_tickers = []    # 雲の上でのゴールデンクロス
        dc_upper_cloud_tickers = []    # 雲の上でのデッドクロス
        dc_under_cloud_tickers = []    # 雲の下でのデッドクロス
        
        # 各銘柄について個別にクロス判定を実行
        for ticker in all_tickers:
            try:
                # 個別銘柄のシグナルファイルを読み込む
                ticker_signal_file = os.path.join(input_dir, f"{ticker}_signal.csv")
                
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
                
                # 前日と当日の転換線・基準線データを取得
                prev_tenkan = recent_data.iloc[0]['Ichimoku_Tenkan']
                prev_kijun = recent_data.iloc[0]['Ichimoku_Kijun']
                curr_tenkan = recent_data.iloc[1]['Ichimoku_Tenkan']
                curr_kijun = recent_data.iloc[1]['Ichimoku_Kijun']
                
                # 雲の状態を取得
                curr_above_cloud = recent_data.iloc[1]['Ichimoku_Above_Cloud']
                curr_below_cloud = recent_data.iloc[1]['Ichimoku_Below_Cloud']
                
                # 遅行線の状態を取得
                curr_chikou_above_price = recent_data.iloc[1]['Ichimoku_Chikou_Above_Price']
                curr_chikou_below_price = recent_data.iloc[1]['Ichimoku_Chikou_Below_Price']
                
                # 先行スパンを取得
                curr_senkou_a = recent_data.iloc[1]['Ichimoku_SenkouA']
                curr_senkou_b = recent_data.iloc[1]['Ichimoku_SenkouB']
                
                # NaN値のチェック
                if (pd.isna(prev_tenkan) or pd.isna(prev_kijun) or 
                    pd.isna(curr_tenkan) or pd.isna(curr_kijun)):
                    continue
                
                # ゴールデンクロスの判定（前日: 転換線 <= 基準線、当日: 転換線 > 基準線）
                golden_cross = prev_tenkan <= prev_kijun and curr_tenkan > curr_kijun
                
                # デッドクロスの判定（前日: 転換線 >= 基準線、当日: 転換線 < 基準線）
                dead_cross = prev_tenkan >= prev_kijun and curr_tenkan < curr_kijun
                
                # 最新データから必要な情報を取得
                current_row = df[df['Ticker'] == ticker].iloc[0]
                
                # 基本的な株式情報
                base_stock_info = {
                    'Ticker': ticker,
                    'Company': current_row['Company'],
                    'Theme': current_row['Theme'],
                    '終値': current_row['Close'],
                    '転換線': curr_tenkan,
                    '基準線': curr_kijun,
                    '前日転換線': prev_tenkan,
                    '前日基準線': prev_kijun
                }
                
                # 抵抗線の目安を雲の位置に基づいて計算
                # 雲の上：先行スパンの低い方（雲の下限が抵抗線）
                # 雲の下：先行スパンの高い方（雲の上限が抵抗線）
                # 雲の中：先行スパンの中間値
                if curr_above_cloud:
                    resistance_level = min(curr_senkou_a, curr_senkou_b) if not (pd.isna(curr_senkou_a) or pd.isna(curr_senkou_b)) else 0
                elif curr_below_cloud:
                    resistance_level = max(curr_senkou_a, curr_senkou_b) if not (pd.isna(curr_senkou_a) or pd.isna(curr_senkou_b)) else 0
                else:
                    # 雲の中の場合は中間値
                    resistance_level = (curr_senkou_a + curr_senkou_b) / 2 if not (pd.isna(curr_senkou_a) or pd.isna(curr_senkou_b)) else 0
                
                # 各条件に応じて分類
                if golden_cross and curr_below_cloud and curr_chikou_above_price:
                    stock_info = base_stock_info.copy()
                    stock_info['抵抗線の目安'] = resistance_level
                    gc_under_cloud_tickers.append(stock_info)
                    logger.info(f"銘柄 {ticker}: 雲の下でゴールデンクロス + 遅行線条件満足")
                elif golden_cross and curr_above_cloud and curr_chikou_above_price:
                    stock_info = base_stock_info.copy()
                    stock_info['抵抗線の目安'] = resistance_level
                    gc_upper_cloud_tickers.append(stock_info)
                    logger.info(f"銘柄 {ticker}: 雲の上でゴールデンクロス + 遅行線条件満足")
                elif dead_cross and curr_above_cloud and curr_chikou_below_price:
                    stock_info = base_stock_info.copy()
                    stock_info['抵抗線の目安'] = resistance_level
                    dc_upper_cloud_tickers.append(stock_info)
                    logger.info(f"銘柄 {ticker}: 雲の上でデッドクロス + 遅行線条件満足")
                elif dead_cross and curr_below_cloud and curr_chikou_below_price:
                    stock_info = base_stock_info.copy()
                    stock_info['抵抗線の目安'] = resistance_level
                    dc_under_cloud_tickers.append(stock_info)
                    logger.info(f"銘柄 {ticker}: 雲の下でデッドクロス + 遅行線条件満足")
                
                # 条件を満たさなかった場合のログ出力（デバッグ用）
                if golden_cross or dead_cross:
                    if golden_cross and not curr_chikou_above_price:
                        logger.debug(f"銘柄 {ticker}: ゴールデンクロスだが遅行線条件不足")
                    elif dead_cross and not curr_chikou_below_price:
                        logger.debug(f"銘柄 {ticker}: デッドクロスだが遅行線条件不足")
                    
            except Exception as e:
                logger.error(f"銘柄 {ticker} の処理中にエラーが発生しました: {str(e)}")
                continue
        
        # === 雲の下でのゴールデンクロス銘柄をCSVに出力 ===
        if gc_under_cloud_tickers:
            gc_under_cloud_df = pd.DataFrame(gc_under_cloud_tickers)
            gc_under_cloud_df = format_ichimoku_output(gc_under_cloud_df)
            
            output_file = os.path.join(output_dir, "ichimoku_GC_under_cloud.csv")
            gc_under_cloud_df.to_csv(output_file, index=False)
            logger.info(f"雲の下ゴールデンクロス+遅行線条件満足銘柄: {len(gc_under_cloud_tickers)}件を {output_file} に出力しました")
        else:
            create_empty_ichimoku_file(os.path.join(output_dir, "ichimoku_GC_under_cloud.csv"))
            logger.info("雲の下ゴールデンクロス+遅行線条件満足銘柄: 0件（空ファイルを出力）")
        
        # === 雲の上でのゴールデンクロス銘柄をCSVに出力 ===
        if gc_upper_cloud_tickers:
            gc_upper_cloud_df = pd.DataFrame(gc_upper_cloud_tickers)
            gc_upper_cloud_df = format_ichimoku_output(gc_upper_cloud_df)
            
            output_file = os.path.join(output_dir, "ichimoku_GC_upper_cloud.csv")
            gc_upper_cloud_df.to_csv(output_file, index=False)
            logger.info(f"雲の上ゴールデンクロス+遅行線条件満足銘柄: {len(gc_upper_cloud_tickers)}件を {output_file} に出力しました")
        else:
            create_empty_ichimoku_file(os.path.join(output_dir, "ichimoku_GC_upper_cloud.csv"))
            logger.info("雲の上ゴールデンクロス+遅行線条件満足銘柄: 0件（空ファイルを出力）")
        
        # === 雲の上でのデッドクロス銘柄をCSVに出力 ===
        if dc_upper_cloud_tickers:
            dc_upper_cloud_df = pd.DataFrame(dc_upper_cloud_tickers)
            dc_upper_cloud_df = format_ichimoku_output(dc_upper_cloud_df)
            
            output_file = os.path.join(output_dir, "ichimoku_DC_upper_cloud.csv")
            dc_upper_cloud_df.to_csv(output_file, index=False)
            logger.info(f"雲の上デッドクロス+遅行線条件満足銘柄: {len(dc_upper_cloud_tickers)}件を {output_file} に出力しました")
        else:
            create_empty_ichimoku_file(os.path.join(output_dir, "ichimoku_DC_upper_cloud.csv"))
            logger.info("雲の上デッドクロス+遅行線条件満足銘柄: 0件（空ファイルを出力）")
        
        # === 雲の下でのデッドクロス銘柄をCSVに出力 ===
        if dc_under_cloud_tickers:
            dc_under_cloud_df = pd.DataFrame(dc_under_cloud_tickers)
            dc_under_cloud_df = format_ichimoku_output(dc_under_cloud_df)
            
            output_file = os.path.join(output_dir, "ichimoku_DC_under_cloud.csv")
            dc_under_cloud_df.to_csv(output_file, index=False)
            logger.info(f"雲の下デッドクロス+遅行線条件満足銘柄: {len(dc_under_cloud_tickers)}件を {output_file} に出力しました")
        else:
            create_empty_ichimoku_file(os.path.join(output_dir, "ichimoku_DC_under_cloud.csv"))
            logger.info("雲の下デッドクロス+遅行線条件満足銘柄: 0件（空ファイルを出力）")
        
        return True
        
    except Exception as e:
        logger.error(f"一目均衡表クロス銘柄抽出処理中にエラーが発生しました: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def format_ichimoku_output(df: pd.DataFrame) -> pd.DataFrame:
    """
    一目均衡表出力データの書式を整える
    
    Args:
        df: 一目均衡表データのデータフレーム
        
    Returns:
        pd.DataFrame: 書式を整えたデータフレーム
    """
    # 数値データの小数点以下桁数を調整
    df['転換線'] = df['転換線'].round(2)
    df['基準線'] = df['基準線'].round(2)
    df['前日転換線'] = df['前日転換線'].round(2)
    df['前日基準線'] = df['前日基準線'].round(2)
    df['抵抗線の目安'] = df['抵抗線の目安'].round(2)
    
    # 終値の表示形式を調整
    df['終値'] = df['終値'].apply(
        lambda x: int(x) if x == int(x) else round(x, 1)
    )
    
    # テーマ列を日本語に変更
    if 'Theme' in df.columns:
        df = df.rename(columns={'Theme': 'テーマ'})
    
    # 列の順序を調整
    columns_order = [
        'Ticker', 'Company', 'テーマ', '終値', '転換線', '基準線', 
        '前日転換線', '前日基準線', '抵抗線の目安'
    ]
    
    return df[columns_order]


def create_empty_ichimoku_file(file_path: str):
    """
    空の一目均衡表ファイルを作成する
    
    Args:
        file_path: 作成するファイルのパス
    """
    empty_df = pd.DataFrame(columns=[
        'Ticker', 'Company', 'テーマ', '終値', '転換線', '基準線', 
        '前日転換線', '前日基準線', '抵抗線の目安'
    ])
    empty_df.to_csv(file_path, index=False)


# メイン関数の更新版
def extract_all_ichimoku_signals(is_test_mode: bool = False) -> bool:
    """
    すべてのシグナル抽出処理を実行します
    
    Args:
        is_test_mode (bool): テストモードの場合はTrue、通常モードの場合はFalse
        
    Returns:
        bool: すべての処理が成功した場合はTrue、エラーが発生した場合はFalse
    """
    import config
    
    # StockSignal名前付きロガーを取得
    logger = logging.getLogger("StockSignal")
    logger.info("すべてのシグナル抽出処理を開始します")
    
    try:
        # 基本的なシグナル抽出
        if not extract_signals(is_test_mode):
            logger.error("基本シグナル抽出処理が失敗しました")
            return False
        
        # 強気トレンド抽出
        if not extract_strong_buying_trend(is_test_mode):
            logger.error("強気トレンド抽出処理が失敗しました")
            return False
        
        # 強気売りトレンド抽出
        if not extract_strong_selling_trend(is_test_mode):
            logger.error("強気売りトレンド抽出処理が失敗しました")
            return False
        
        # 三役好転・三役暗転抽出
        if not extract_sanyaku_signals(is_test_mode):
            logger.error("三役好転・三役暗転抽出処理が失敗しました")
            return False
        
        # 一目均衡表クロス抽出
        if not extract_ichimoku_cross_signals(is_test_mode):
            logger.error("一目均衡表クロス抽出処理が失敗しました")
            return False
        
        logger.info("すべてのシグナル抽出処理が正常に完了しました")
        return True
        
    except Exception as e:
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