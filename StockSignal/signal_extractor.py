"""
シグナル抽出モジュール - テクニカル指標CSVから条件に合致する銘柄を抽出

このモジュールは、テクニカル指標の計算結果から、投資判断に使うシグナル銘柄を
抽出する機能を提供します。現在サポートしているシグナルは以下の2種類です：

1. ブレイクアウト銘柄 (identify_breakouts)
   - 直近3か月の前日までの最高値を終値が更新
   - 出来高が10万以上
   - 終値が高値と安値の中間より上
   - 陽線で引けている

2. 押し目狙い銘柄 (extract_push_mark_signals)
   - 中期移動平均線が上昇中
   - 終値が短期移動平均線より上
   - 直近3日以内に短期移動平均線の変動率がマイナスだった日がある
   - 中期移動平均線が長期移動平均線より上
   - 出来高が10万以上
   - 出来高が出来高移動平均線より多い

抽出結果は Result/Breakout.csv / Result/push_mark.csv に出力されます。
"""
import os
import time
import logging
from typing import Dict, Optional

import pandas as pd

import config
from data_loader import load_company_info_map

# yfinanceのインポート（ROE取得用）
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False


# =====================================================================
# ROE情報取得ヘルパー
# =====================================================================

def get_roe_for_ticker(ticker: str, logger: logging.Logger) -> Optional[float]:
    """
    指定された銘柄のROE情報をyfinanceから取得します

    Args:
        ticker: 銘柄コード（例: "7203" または "7203.T"）
        logger: ロガーオブジェクト

    Returns:
        ROE値（パーセンテージ）。取得できない場合は None
    """
    if not YFINANCE_AVAILABLE:
        logger.warning("yfinanceライブラリが利用できません。ROE情報は取得されません。")
        return None

    try:
        ticker_with_suffix = ticker if ticker.endswith('.T') else f"{ticker}.T"
        stock = yf.Ticker(ticker_with_suffix)
        roe = stock.info.get('returnOnEquity')

        if roe is None:
            logger.warning(f"{ticker}: ROE情報が取得できませんでした")
            return None

        return round(roe * 100, 2)

    except Exception as e:
        logger.error(f"{ticker}: ROE取得中にエラーが発生しました: {str(e)}")
        return None


# =====================================================================
# ブレイクアウト銘柄抽出
# =====================================================================

def identify_breakouts(is_test_mode: bool = False) -> bool:
    """
    ブレイクアウト銘柄を抽出してCSVファイルに出力します

    抽出条件:
    1. 最新の終値が直近3か月の「前日までの」最高値を更新している
    2. 出来高が10万以上
    3. 終値が高値と安値の中間より上（上髭が短い）
    4. 陽線である（終値が始値を上回る）

    Args:
        is_test_mode: テストモード時は別ディレクトリのデータを使用

    Returns:
        bool: 処理が成功した場合はTrue、エラー時はFalse
    """
    from datetime import timedelta

    logger = logging.getLogger(__name__)
    logger.info("ブレイク銘柄の抽出処理を開始します...")

    try:
        # 入出力ディレクトリの設定
        if is_test_mode:
            technical_dir = os.path.join(config.TEST_TECHNICAL_DIR, "StockSignal", "TechnicalSignal")
            result_dir = os.path.join(config.TEST_DIR, "Result")
        else:
            technical_dir = config.TECHNICAL_DIR
            result_dir = os.path.join(config.BASE_DIR, "StockSignal", "Result")

        os.makedirs(result_dir, exist_ok=True)

        # 企業情報マッピング
        company_info_map = load_company_info_map(is_test_mode)

        # テクニカル指標ディレクトリ内のCSVファイルを処理
        csv_files = [f for f in os.listdir(technical_dir) if f.endswith('_signal.csv')]
        if not csv_files:
            logger.warning(f"指定されたディレクトリ({technical_dir})にシグナルCSVファイルが見つかりません。")
            return False

        breakout_stocks = []

        for csv_file in csv_files:
            try:
                file_path = os.path.join(technical_dir, csv_file)
                df = pd.read_csv(file_path)

                if df.empty:
                    logger.warning(f"{csv_file}のデータが空です。スキップします。")
                    continue

                if len(df) < 90:  # 約3か月分の営業日
                    logger.warning(f"{csv_file}のデータが不足しています。スキップします。")
                    continue

                df['Date'] = pd.to_datetime(df['Date'])
                latest_date = df['Date'].max()
                three_month_ago = latest_date - timedelta(days=90)

                three_month_data = df[df['Date'] >= three_month_ago]
                latest_data = df.iloc[-1]
                # 前日までのデータを抽出（最新日を除く）
                previous_data = three_month_data[three_month_data['Date'] < latest_date]

                # 条件1: 最新の終値が直近3か月の「前日までの」最高値を更新
                if previous_data.empty:
                    condition1 = False
                else:
                    condition1 = latest_data['Close'] >= previous_data['High'].max()

                # 条件2: 出来高が10万以上
                condition2 = latest_data['Volume'] >= 100000

                # 条件3: 終値が高値と安値の中間より上（上髭が短い）
                mid_price = (latest_data['High'] + latest_data['Low']) / 2
                condition3 = latest_data['Close'] > mid_price

                # 条件4: 陽線である（終値 > 始値）
                condition4 = latest_data['Close'] > latest_data['Open']

                # 上髭の長さ（結果CSVに記載するため計算）
                high_diff_percent = (latest_data['High'] - latest_data['Close']) / latest_data['Open'] * 100

                ticker = csv_file.split('_')[0]
                logger.debug(f"銘柄: {ticker} / C1:{condition1} C2:{condition2} C3:{condition3} C4:{condition4}")

                if not (condition1 and condition2 and condition3 and condition4):
                    continue

                company_info = company_info_map.get(ticker, {'company': '', 'theme': ''})
                breakout_result = {
                    'Ticker': ticker,
                    'Company': company_info.get('company', ''),
                    'Theme': company_info.get('theme', ''),
                    'Close': latest_data['Close'],
                    'Previous_High': previous_data['High'].max() if not previous_data.empty else None,
                    'Upper_Shadow_Pct': high_diff_percent,
                }

                if 'BB_Upper' in df.columns and pd.notna(latest_data['BB_Upper']):
                    breakout_result['BB_Upper'] = latest_data['BB_Upper']

                breakout_stocks.append(breakout_result)
                logger.info(f"ブレイク銘柄を検出: {ticker} - {company_info.get('company', '')} ({company_info.get('theme', '')})")

            except Exception as e:
                logger.error(f"{csv_file}の処理中にエラーが発生しました: {str(e)}")

        # 結果をDataFrameに変換して出力
        result_df = pd.DataFrame(breakout_stocks)

        if result_df.empty:
            logger.info("条件に一致する銘柄は見つかりませんでした。")
            result_df = pd.DataFrame(columns=[
                'Ticker', 'Company', 'Theme', 'Close',
                'Previous_High', 'Upper_Shadow_Pct', 'BB_Upper'
            ])
        else:
            column_rename = {
                'Theme': 'テーマ',
                'Close': '終値',
                'Previous_High': '前日までの最高値',
                'Upper_Shadow_Pct': '上髭の長さ(%)',
            }
            if 'BB_Upper' in result_df.columns:
                column_rename['BB_Upper'] = 'BB上限(+2σ)'

            result_df = result_df.rename(columns=column_rename)

            # 終値の表示形式（整数 or 小数点1桁）
            result_df['終値'] = result_df['終値'].apply(
                lambda x: int(x) if x == int(x) else round(x, 1)
            )
            result_df['前日までの最高値'] = result_df['前日までの最高値'].round(2)
            result_df['上髭の長さ(%)'] = result_df['上髭の長さ(%)'].round(2)

            if 'BB上限(+2σ)' in result_df.columns:
                result_df['BB上限(+2σ)'] = result_df['BB上限(+2σ)'].round(2)

            # ROE情報の付加
            if YFINANCE_AVAILABLE:
                logger.info("ROE情報の取得を開始します...")
                result_df['ROE(%)'] = None

                for index, row in result_df.iterrows():
                    ticker = str(row['Ticker'])
                    logger.info(f"ROE取得中 ({index + 1}/{len(result_df)}): {ticker} - {row['Company']}")
                    roe = get_roe_for_ticker(ticker, logger)
                    if roe is not None:
                        result_df.at[index, 'ROE(%)'] = roe
                        logger.info(f"  ROE: {roe}%")
                    else:
                        logger.warning(f"  ROE取得失敗")
                    time.sleep(0.5)  # API制限回避

                roe_success_count = result_df['ROE(%)'].notna().sum()
                logger.info(f"ROE情報の取得が完了しました。成功: {roe_success_count}/{len(result_df)} 銘柄")

            # 列の順序: Ticker, Company, テーマ, 終値, ROE(%), BB上限, 前日までの最高値, 上髭の長さ
            columns_order = ['Ticker', 'Company', 'テーマ', '終値']
            if 'ROE(%)' in result_df.columns:
                columns_order.append('ROE(%)')
            if 'BB上限(+2σ)' in result_df.columns:
                columns_order.append('BB上限(+2σ)')
            columns_order.extend(['前日までの最高値', '上髭の長さ(%)'])

            available_columns = [col for col in columns_order if col in result_df.columns]
            result_df = result_df[available_columns]

        output_path = os.path.join(result_dir, "Breakout.csv")
        result_df.to_csv(output_path, index=False, encoding='utf-8-sig')

        logger.info(f"ブレイク銘柄の抽出が完了しました。検出数: {len(result_df)}")
        logger.info(f"結果ファイルの保存先: {output_path}")
        return True

    except Exception as e:
        logger.error(f"ブレイク銘柄の抽出処理中にエラーが発生しました: {str(e)}")
        return False


# =====================================================================
# 押し目銘柄抽出
# =====================================================================

def extract_push_mark_signals(is_test_mode: bool = False) -> bool:
    """
    押し目銘柄を抽出してCSVファイルに出力します

    抽出条件:
    1. 中期移動平均線が上昇中（前日より高い）
    2. 終値が短期移動平均線より上
    3. 直近3日以内に短期移動平均線の変動率がマイナスだった日がある
    4. 中期移動平均線が長期移動平均線より上
    5. 出来高が10万以上
    6. 出来高が出来高移動平均線より多い

    Args:
        is_test_mode: テストモード時は別ディレクトリのデータを使用

    Returns:
        bool: 処理が成功した場合はTrue、エラー時はFalse
    """
    logger = logging.getLogger("StockSignal")
    logger.info("押し目銘柄の抽出を開始します")

    try:
        # 入出力ディレクトリの設定
        if is_test_mode:
            input_dir = os.path.join(config.TEST_DIR, "StockSignal", "TechnicalSignal")
            output_dir = os.path.join(config.TEST_DIR, "Result")
        else:
            input_dir = os.path.join(config.BASE_DIR, "StockSignal", "TechnicalSignal")
            output_dir = os.path.join(config.BASE_DIR, "StockSignal", "Result")

        os.makedirs(output_dir, exist_ok=True)

        input_file = os.path.join(input_dir, config.LATEST_SIGNAL_FILE)
        if not os.path.exists(input_file):
            logger.error(f"ファイルが見つかりません: {input_file}")
            return False

        logger.info(f"{input_file} を読み込みます")
        latest_df = pd.read_csv(input_file, index_col=0, parse_dates=True)

        # 移動平均線のカラム名 (MA_PERIODS = [5, 20, 60])
        short_ma = f'MA{config.MA_PERIODS[0]}'
        mid_ma = f'MA{config.MA_PERIODS[1]}'
        long_ma = f'MA{config.MA_PERIODS[2]}'
        volume_ma = f'Volume_MA{config.MA_PERIODS[1]}'

        required_columns = ['Ticker', 'Company', 'Theme']
        missing_columns = [col for col in required_columns if col not in latest_df.columns]
        if missing_columns:
            logger.error(f"必要なカラムがCSVファイルに見つかりません: {missing_columns}")
            return False

        all_tickers = latest_df['Ticker'].unique()
        logger.info(f"処理対象の全銘柄数: {len(all_tickers)}")

        push_mark_tickers = []

        for ticker in all_tickers:
            try:
                ticker_signal_file = os.path.join(input_dir, f"{ticker}_signal.csv")
                if not os.path.exists(ticker_signal_file):
                    continue

                ticker_df = pd.read_csv(ticker_signal_file, index_col=0, parse_dates=True)
                if len(ticker_df) < 3:  # 3日以内の変動率チェックが必要
                    continue

                required_cols = ['Close', 'Volume', short_ma, mid_ma, long_ma, volume_ma]
                if not all(col in ticker_df.columns for col in required_cols):
                    continue

                latest_row = ticker_df.iloc[-1]
                prev_row = ticker_df.iloc[-2]

                # 条件1: 中期移動平均線が上昇中
                condition1 = latest_row[mid_ma] > prev_row[mid_ma]

                # 条件2: 終値が短期移動平均線より上
                condition2 = latest_row['Close'] > latest_row[short_ma]

                # 条件3: 3日以内に短期移動平均線の変動率がマイナスだった日がある
                recent_3days = ticker_df.tail(3)
                condition3 = False
                for i in range(1, len(recent_3days)):
                    prev_ma = recent_3days.iloc[i-1][short_ma]
                    curr_ma = recent_3days.iloc[i][short_ma]
                    if prev_ma > 0:
                        change_rate = ((curr_ma - prev_ma) / prev_ma) * 100
                        if change_rate < 0:
                            condition3 = True
                            break

                # 条件4: 中期移動平均線が長期移動平均線より上
                condition4 = latest_row[mid_ma] > latest_row[long_ma]

                # 条件5: 出来高が10万以上
                condition5 = latest_row['Volume'] >= 100000

                # 条件6: 出来高が出来高移動平均線より多い
                condition6 = latest_row['Volume'] > latest_row[volume_ma]

                if not (condition1 and condition2 and condition3 and condition4 and condition5 and condition6):
                    continue

                company_info = latest_df[latest_df['Ticker'] == ticker].iloc[0]
                push_mark_tickers.append({
                    'Ticker': ticker,
                    'Company': company_info.get('Company', ''),
                    'テーマ': company_info.get('Theme', ''),
                    '最新の終値': latest_row['Close'],
                    '短期移動平均': latest_row[short_ma],
                    '中期移動平均': latest_row[mid_ma],
                    '長期移動平均': latest_row[long_ma],
                    '出来高': latest_row['Volume'],
                    '出来高移動平均': latest_row[volume_ma],
                })

            except Exception as e:
                logger.warning(f"銘柄 {ticker} の処理中にエラーが発生しました: {str(e)}")
                continue

        # 結果を出力
        output_file = os.path.join(output_dir, "push_mark.csv")

        if push_mark_tickers:
            push_mark_df = pd.DataFrame(push_mark_tickers)
            push_mark_df['短期移動平均'] = push_mark_df['短期移動平均'].round(2)
            push_mark_df['中期移動平均'] = push_mark_df['中期移動平均'].round(2)
            push_mark_df['長期移動平均'] = push_mark_df['長期移動平均'].round(2)
            push_mark_df['出来高'] = push_mark_df['出来高'].round(2)
            push_mark_df['出来高移動平均'] = push_mark_df['出来高移動平均'].round(2)
            push_mark_df['最新の終値'] = push_mark_df['最新の終値'].apply(
                lambda x: int(x) if x == int(x) else round(x, 1)
            )
            push_mark_df.to_csv(output_file, index=False, encoding='utf-8-sig')
            logger.info(f"押し目銘柄: {len(push_mark_df)}件を {output_file} に出力しました")
        else:
            logger.info("条件を満たす押し目銘柄は見つかりませんでした")
            empty_df = pd.DataFrame(columns=[
                'Ticker', 'Company', 'テーマ', '最新の終値',
                '短期移動平均', '中期移動平均', '長期移動平均',
                '出来高', '出来高移動平均'
            ])
            empty_df.to_csv(output_file, index=False, encoding='utf-8-sig')
            logger.info(f"空の押し目ファイルを {output_file} に出力しました")

        return True

    except Exception as e:
        logger.error(f"押し目銘柄抽出処理中にエラーが発生しました: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


# =====================================================================
# 単独実行用エントリーポイント
# =====================================================================

if __name__ == "__main__":
    import sys
    import argparse

    from data_loader import setup_logger

    parser = argparse.ArgumentParser(description='シグナル抽出ツール（ブレイクアウト・押し目）')
    parser.add_argument('--test', action='store_true', help='テストモードで実行')
    parser.add_argument('--type', choices=['breakout', 'push_mark', 'all'], default='breakout',
                        help='抽出するシグナルの種類（デフォルト: breakout）')
    args = parser.parse_args()

    logger = setup_logger(args.test)

    if args.type == 'breakout':
        success = identify_breakouts(args.test)
    elif args.type == 'push_mark':
        success = extract_push_mark_signals(args.test)
    else:  # all
        success = identify_breakouts(args.test) and extract_push_mark_signals(args.test)

    sys.exit(0 if success else 1)
