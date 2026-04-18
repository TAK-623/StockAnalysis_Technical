"""
シグナル抽出モジュール - 押し目銘柄の抽出

このモジュールは、テクニカル分析によって生成されたシグナル情報から、
押し目買いの候補銘柄を抽出・出力する機能を提供します。
単独実行も、他のモジュールからの呼び出しも可能です。

出力ファイル：
- push_mark.csv: 押し目狙い銘柄
"""
import os
import pandas as pd
import logging
from typing import Optional


def extract_push_mark_signals(is_test_mode: bool = False) -> bool:
    """
    latest_signal.csvから押し目の銘柄を抽出してCSVファイルに出力します
    
    以下の条件をすべて満たす銘柄を抽出します：
    1. 中期移動平均線が上昇中
    2. 終値が短期移動平均線よりも上にある
    3. 3日以内に短期移動平均線の変動率はマイナスだった日がある
    4. 中期移動線が長期移動平均線よりも上にある
    5. 出来高が10万以上
    6. 出来高が出来高移動平均線よりも上
    
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
    logger.info("中期移動平均線が上昇中")
    logger.info("終値が短期移動平均線よりも上にある")
    logger.info("3日以内に短期移動平均線の変動率はマイナスだった日がある")
    logger.info("中期移動線が長期移動平均線よりも上にある")
    logger.info("出来高が10万以上")
    logger.info("出来高が出来高移動平均線よりも上")
    
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
        
        # CSVの読み込み（最新シグナルファイルから銘柄リストを取得）
        logger.info(f"{input_file} を読み込みます")
        latest_df = pd.read_csv(input_file, index_col=0, parse_dates=True)
        
        # 各銘柄の短期・中期の移動平均を取得
        # 設定ファイルから移動平均期間を取得 (MA_PERIODS = [5, 20, 60])
        short_ma = f'MA{config.MA_PERIODS[0]}'  # 短期移動平均 (MA5)
        mid_ma = f'MA{config.MA_PERIODS[1]}'    # 中期移動平均 (MA20)
        long_ma = f'MA{config.MA_PERIODS[2]}'    # 長期移動平均 (MA60)
        volume_ma = f'Volume_MA{config.MA_PERIODS[1]}'  # 出来高移動平均 (Volume_MA20)
        
        # 必要なカラムの存在確認
        required_columns = ['Ticker', 'Company', 'Theme']
        missing_columns = [col for col in required_columns if col not in latest_df.columns]
        if missing_columns:
            logger.error(f"必要なカラムがCSVファイルに見つかりません: {missing_columns}")
            return False

        logger.info("各銘柄の条件判定を開始します")

        # 全銘柄のティッカーリストを取得
        all_tickers = latest_df['Ticker'].unique()
        logger.info(f"処理対象の全銘柄数: {len(all_tickers)}")
        
        # 押し目銘柄を格納するリスト
        push_mark_tickers = []
        
        # 各銘柄の全期間データを読み込んで条件判定
        for ticker in all_tickers:
            try:
                # 各銘柄の全期間データファイルを読み込む
                ticker_signal_file = os.path.join(input_dir, f"{ticker}_signal.csv")
                
                if not os.path.exists(ticker_signal_file):
                    continue
                
                # 全期間データを読み込む
                ticker_df = pd.read_csv(ticker_signal_file, index_col=0, parse_dates=True)
                
                # データが3行未満の場合はスキップ（3日以内の変動率チェックができない）
                if len(ticker_df) < 3:
                    continue
                
                # 最新日と前日のデータを取得
                latest_row = ticker_df.iloc[-1]
                prev_row = ticker_df.iloc[-2]
                
                # 必要なカラムの存在確認
                required_cols = ['Close', 'Volume', short_ma, mid_ma, long_ma, volume_ma]
                if not all(col in ticker_df.columns for col in required_cols):
                    continue
                
                # 条件1: 中期移動平均線が上昇中（前日より高い）
                condition1 = latest_row[mid_ma] > prev_row[mid_ma]
                
                # 条件2: 終値が短期移動平均線よりも上にある
                condition2 = latest_row['Close'] > latest_row[short_ma]
                
                # 条件3: 3日以内に短期移動平均線の変動率がマイナスだった日がある
                # 最新3日分のデータを取得
                recent_3days = ticker_df.tail(3)
                condition3 = False
                for i in range(1, len(recent_3days)):
                    prev_ma = recent_3days.iloc[i-1][short_ma]
                    curr_ma = recent_3days.iloc[i][short_ma]
                    # 変動率を計算: (当日 - 前日) / 前日 * 100
                    if prev_ma > 0:  # ゼロ除算を防ぐ
                        change_rate = ((curr_ma - prev_ma) / prev_ma) * 100
                        if change_rate < 0:  # マイナス（下落）の場合
                            condition3 = True
                            break
                
                # 条件4: 中期移動線が長期移動平均線よりも上にある
                condition4 = latest_row[mid_ma] > latest_row[long_ma]
                
                # 条件5: 出来高が10万以上
                condition5 = latest_row['Volume'] >= 100000
                
                # 条件6: 出来高が出来高移動平均線よりも上
                condition6 = latest_row['Volume'] > latest_row[volume_ma]
                
                # すべての条件を満たす場合
                if condition1 and condition2 and condition3 and condition4 and condition5 and condition6:
                    # 会社情報を取得
                    company_info = latest_df[latest_df['Ticker'] == ticker].iloc[0]
                    company = company_info.get('Company', '')
                    theme = company_info.get('Theme', '')
                    
                    # 押し目銘柄情報を追加
                    push_mark_tickers.append({
                        'Ticker': ticker,
                        'Company': company,
                        'テーマ': theme,
                        '最新の終値': latest_row['Close'],
                        '短期移動平均': latest_row[short_ma],
                        '中期移動平均': latest_row[mid_ma],
                        '長期移動平均': latest_row[long_ma],
                        '出来高': latest_row['Volume'],
                        '出来高移動平均': latest_row[volume_ma]
                    })
                    
            except Exception as e:
                logger.warning(f"銘柄 {ticker} の処理中にエラーが発生しました: {str(e)}")
                continue
        
        # 押し目銘柄をデータフレームに変換
        if push_mark_tickers:
            push_mark_df = pd.DataFrame(push_mark_tickers)
            
            # 数値データの小数点以下桁数を調整
            push_mark_df['短期移動平均'] = push_mark_df['短期移動平均'].round(2)
            push_mark_df['中期移動平均'] = push_mark_df['中期移動平均'].round(2)
            push_mark_df['長期移動平均'] = push_mark_df['長期移動平均'].round(2)
            push_mark_df['出来高'] = push_mark_df['出来高'].round(2)
            push_mark_df['出来高移動平均'] = push_mark_df['出来高移動平均'].round(2)
            
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
                logger.info(f"  {i+1}. {stock['Ticker']} {stock['Company']} ({stock['テーマ']}) "
                           f"終値: {stock['最新の終値']}, "
                           f"短期MA: {stock['短期移動平均']:.2f}, "
                           f"中期MA: {stock['中期移動平均']:.2f}",
                           f"長期MA: {stock['長期移動平均']:.2f}",
                           f"出来高: {stock['出来高']}",
                           f"出来高移動平均: {stock['出来高移動平均']:.2f}")
        else:
            logger.info("条件を満たす押し目銘柄は見つかりませんでした")
            
            # 空のデータフレームを作成して出力
            empty_df = pd.DataFrame(columns=[
                'Ticker', 'Company', 'テーマ', '最新の終値', '短期移動平均', '中期移動平均', '長期移動平均', '出来高', '出来高移動平均'
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


# このファイルが直接実行された場合（モジュールとしてインポートされた場合は実行されない）
if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='押し目銘柄抽出ツール')
    parser.add_argument('--test', action='store_true', help='テストモードで実行')
    args = parser.parse_args()
    
    from data_loader import setup_logger
    logger = setup_logger(args.test)
    
    success = extract_push_mark_signals(args.test)
    sys.exit(0 if success else 1)
