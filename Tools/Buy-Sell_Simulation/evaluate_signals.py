import os
import sys
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import glob
from pathlib import Path
import time
import re

def get_next_business_day(date_str):
    """入力された日付(yyyymmdd)の翌営業日を取得する"""
    date = datetime.strptime(date_str, '%Y%m%d')
    next_day = date + timedelta(days=1)
    
    # 土曜日なら2日後(月曜日)、日曜日なら1日後(月曜日)を返す
    if next_day.weekday() == 5:  # 土曜日
        return next_day + timedelta(days=2)
    elif next_day.weekday() == 6:  # 日曜日
        return next_day + timedelta(days=1)
    else:
        return next_day

def calculate_profit_loss(input_file, date_str, evaluation_date_str=None):
    """指定されたファイルと日付で評価損益を計算する
    
    Args:
        input_file: 入力CSVファイルのパス
        date_str: 売買シグナルの出た日（yyyymmdd形式）
        evaluation_date_str: 評価日（yyyymmdd形式、Noneの場合は実行時点の最新値を使用）
    """
    # CSVファイルを読み込む
    print(f"ファイル {os.path.basename(input_file)} を読み込んでいます...")
    df = pd.read_csv(input_file, encoding='utf-8')
    
    # 結果を格納するデータフレームを初期化
    result_df = pd.DataFrame()
    
    # 翌営業日を取得
    next_business_day = get_next_business_day(date_str)
    next_business_day_str = next_business_day.strftime('%Y-%m-%d')
    
    # 評価終了日を設定
    if evaluation_date_str:
        # 評価日が指定されている場合、その翌日を終了日として設定（その日までのデータを含めるため）
        evaluation_date = datetime.strptime(evaluation_date_str, '%Y%m%d')
        end_date = (evaluation_date + timedelta(days=1)).strftime('%Y-%m-%d')
        print(f"評価日 {evaluation_date_str} のClose値を使用して評価します")
    else:
        # 評価日が指定されていない場合は現在の日付
        end_date = datetime.now().strftime('%Y-%m-%d')
        print(f"実行時点の最新Close値を使用して評価します")
    
    # 総銘柄数を取得して進捗表示に使用
    total_tickers = len(df)
    print(f"合計 {total_tickers} 銘柄の処理を開始します...")
    
    # 各銘柄について処理
    for idx, row in df.iterrows():
        ticker = str(row['Ticker'])
        company = row['Company']
        
        # 進捗表示
        print(f"処理中 ({idx+1}/{total_tickers}): {ticker} - {company}")
        
        # ティッカーシンボルの調整（日本株の場合は.Tを追加）
        if len(ticker) == 4 and ticker.isdigit():  # 日本株の銘柄コードは通常4桁
            ticker_symbol = f"{ticker}.T"
        else:
            ticker_symbol = ticker
        
        try:
            # yfinanceで株価データを取得
            print(f"  yfinanceから {ticker_symbol} の株価データを取得中...")
            stock_data = yf.download(ticker_symbol, start=next_business_day_str, end=end_date, progress=False)
            
            if not stock_data.empty:
                # 翌営業日のOpen値を取得
                next_day_open = None
                next_day_date = None
                
                for idx_date, data in stock_data.iterrows():
                    if idx_date.strftime('%Y-%m-%d') >= next_business_day_str:
                        next_day_open = float(data['Open'])  # 明示的に浮動小数点に変換
                        next_day_date = idx_date.strftime('%Y-%m-%d')
                        break
                
                # 評価日または最新のClose値を取得
                if evaluation_date_str:
                    # 評価日のClose値を探す
                    evaluation_close = None
                    evaluation_date_actual = None
                    
                    # 評価日付から近い日を検索 (正確な日付が存在しない可能性があるため)
                    target_date = datetime.strptime(evaluation_date_str, '%Y%m%d')
                    
                    # 指定された評価日以前の最新のデータを探す
                    valid_dates = [d for d in stock_data.index if d <= target_date]
                    
                    if valid_dates:
                        latest_valid_date = max(valid_dates)
                        evaluation_close = float(stock_data.loc[latest_valid_date]['Close'])
                        evaluation_date_actual = latest_valid_date.strftime('%Y%m%d')
                        evaluation_date_display = latest_valid_date.strftime('%Y-%m-%d')
                    else:
                        print(f"  警告: {ticker}の{evaluation_date_str}以前のClose値が取得できませんでした")
                        continue
                else:
                    # 最新のClose値を取得
                    evaluation_close = float(stock_data.iloc[-1]['Close'])  # 明示的に浮動小数点に変換
                    evaluation_date_actual = stock_data.index[-1].strftime('%Y%m%d')
                    evaluation_date_display = stock_data.index[-1].strftime('%Y-%m-%d')
                
                # 評価額と評価損益率を計算
                if next_day_open is not None and evaluation_close is not None:
                    evaluation_amount = evaluation_close - next_day_open
                    evaluation_rate = (evaluation_amount / next_day_open) * 100
                    
                    # 結果を追加
                    result_df = pd.concat([result_df, pd.DataFrame({
                        'Ticker': [ticker],
                        'Company': [company],
                        '評価額': [round(evaluation_amount, 2)],
                        '評価損益率(%)': [round(evaluation_rate, 2)],
                        '売買の日': [date_str],
                        '翌営業日のOpen値': [round(next_day_open, 2)],
                        '評価日': [evaluation_date_actual],
                        '評価日のClose値': [round(evaluation_close, 2)]
                    })], ignore_index=True)
                    
                    print(f"  評価額: {round(evaluation_amount, 2)}, 評価損益率: {round(evaluation_rate, 2)}%")
                    print(f"  （{next_day_date}のOpen値: {round(next_day_open, 2)} → {evaluation_date_display}のClose値: {round(evaluation_close, 2)}）")
                else:
                    if next_day_open is None:
                        print(f"  警告: {ticker}の{next_business_day_str}のOpen値が取得できませんでした")
                    if evaluation_close is None:
                        print(f"  警告: {ticker}の評価日のClose値が取得できませんでした")
            else:
                print(f"  警告: {ticker}の株価データが取得できませんでした")
        except Exception as e:
            print(f"  エラー: {ticker}の処理中にエラーが発生しました - {str(e)}")
        
        # APIリクエスト制限を考慮して少し待機
        time.sleep(0.2)
    
    return result_df

def generate_summary(result_df, input_filename, output_dir):
    """評価結果のサマリーを作成し、別ファイルに出力する"""
    # 入力ファイル名からサマリーファイル名を生成
    basename = os.path.basename(input_filename)
    basename_lower = basename.lower()  # 小文字に変換して比較
    
    # 複数のファイル名パターンに対応
    if re.search(r'_signal_result_(buy|sell)\.csv', basename_lower):
        # "macd_rci_signal_result_buy.csv" パターン
        match = re.search(r'(.+?)_signal_result_(.+?)\.csv', basename)
        if match:
            indicator_type = match.group(1)  # macd_rci
            signal_type = match.group(2).lower()  # buy または sell
            summary_filename = f"summary_{indicator_type}_{signal_type}.csv"
            is_sell_signal = signal_type == 'sell'
    elif re.search(r'buying', basename_lower):
        # ファイル名に "buying" が含まれる場合は買いシグナル
        file_base = os.path.splitext(basename)[0]
        summary_filename = f"summary_{file_base}.csv"
        is_sell_signal = False
    elif re.search(r'selling', basename_lower):
        # ファイル名に "selling" が含まれる場合は売りシグナル
        file_base = os.path.splitext(basename)[0]
        summary_filename = f"summary_{file_base}.csv"
        is_sell_signal = True
    elif re.search(r'range_break\.csv', basename_lower) or re.search(r'range_brake\.csv', basename_lower):
        # "range_break.csv" または "Range_Brake.csv" パターン
        summary_filename = "summary_range_break.csv"
        is_sell_signal = False  # デフォルトは買いシグナルとして扱う
    else:
        # その他のパターン
        file_base = os.path.splitext(basename)[0]
        summary_filename = f"summary_{file_base}.csv"
        is_sell_signal = False  # デフォルトは買いシグナルとして扱う
    
    summary_path = os.path.join(output_dir, summary_filename)
    
    # サマリーデータを計算
    total_evaluation_amount = result_df['評価額'].sum()
    
    # 総評価損益率（全銘柄の評価額の合計 ÷ 全銘柄の購入価格の合計 × 100）
    total_investment = (result_df['翌営業日のOpen値'] * 1).sum()  # 各銘柄1株ずつと仮定
    total_evaluation_rate = (total_evaluation_amount / total_investment) * 100 if total_investment != 0 else 0
    
    # シグナル正解率の計算（sell の場合と buy の場合で条件を変える）
    total_count = len(result_df)
    
    if is_sell_signal:
        # sell の場合は評価額がマイナスの銘柄が正解
        correct_count = len(result_df[result_df['評価額'] < 0])
        success_message = f"シグナル正解率(売り - マイナスが正解)"
    else:
        # buy の場合は評価額がプラスの銘柄が正解
        correct_count = len(result_df[result_df['評価額'] > 0])
        success_message = f"シグナル正解率(買い - プラスが正解)"
    
    success_rate = (correct_count / total_count) * 100 if total_count > 0 else 0
    
    # サマリーデータフレームを作成
    summary_df = pd.DataFrame({
        '項目': [
            '合計評価額', 
            '合計評価損益率(%)', 
            success_message,
            '全体銘柄数',
            '正解銘柄数'
        ],
        '値': [
            round(total_evaluation_amount, 2),
            round(total_evaluation_rate, 2),
            round(success_rate, 2),
            total_count,
            correct_count
        ]
    })
    
    # CSVファイルに出力
    summary_df.to_csv(summary_path, index=False, encoding='utf-8')
    
    print(f"サマリーファイルを出力しました: {summary_filename}")
    print(f"  合計評価額: {round(total_evaluation_amount, 2)}")
    print(f"  合計評価損益率(%): {round(total_evaluation_rate, 2)}%")
    print(f"  {success_message}(%): {round(success_rate, 2)}% ({correct_count}/{total_count})")
    print(f"  全体銘柄数: {total_count}")
    print(f"  正解銘柄数: {correct_count}")
    
    return summary_path

def main():
    start_time = time.time()
    print("評価損益計算処理を開始します...")
    
    # コマンドライン引数から日付を取得
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("使用方法: python stock_evaluation.py yyyymmdd [評価日yyyymmdd]")
        print("  yyyymmdd: 売買シグナルの出た日")
        print("  評価日: 指定した場合、この日付時点の最新Close値で評価します。指定しない場合は実行時点の最新Close値を使用します。")
        sys.exit(1)
    
    signal_date_str = sys.argv[1]
    print(f"売買シグナルの出た日: {signal_date_str}")
    
    # 第2引数（評価日）があれば取得
    evaluation_date_str = None
    if len(sys.argv) == 3:
        evaluation_date_str = sys.argv[2]
        print(f"評価日: {evaluation_date_str}")
    else:
        print("評価日: 指定なし（実行時点の最新Close値を使用）")
    
    # 日付の形式をチェック
    try:
        datetime.strptime(signal_date_str, '%Y%m%d')
        if evaluation_date_str:
            datetime.strptime(evaluation_date_str, '%Y%m%d')
    except ValueError:
        print("エラー: 日付はyyyymmdd形式で入力してください")
        sys.exit(1)
    
    # 入力フォルダと出力フォルダのパスを設定
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, "InputData")
    output_dir = os.path.join(script_dir, "Output")
    
    print(f"入力フォルダ: {input_dir}")
    print(f"出力フォルダ: {output_dir}")
    
    # 出力フォルダが存在しない場合は作成
    if not os.path.exists(output_dir):
        print(f"出力フォルダを作成します: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)
    
    # 入力フォルダ内のCSVファイルを処理
    input_files = glob.glob(os.path.join(input_dir, "*.csv"))
    
    if not input_files:
        print(f"警告: {input_dir}にCSVファイルが見つかりませんでした")
        sys.exit(0)
    
    print(f"処理対象ファイル数: {len(input_files)}")
    
    for file_idx, input_file in enumerate(input_files, 1):
        try:
            # ファイル名から出力ファイル名を生成
            base_filename = os.path.basename(input_file)
            base_filename_lower = base_filename.lower()
            
            # range_break.csv または Range_Brake.csv の場合は特別な処理
            if re.search(r'range_break\.csv', base_filename_lower) or re.search(r'range_brake\.csv', base_filename_lower):
                output_filename = "range_break_eval.csv"
            else:
                output_filename = os.path.splitext(base_filename)[0] + "_eval.csv"
            
            output_path = os.path.join(output_dir, output_filename)
            
            print(f"\nファイル {file_idx}/{len(input_files)}: {base_filename} の処理を開始します")
            print(f"出力ファイル: {output_filename}")
            
            # 評価損益を計算（評価日パラメータを追加）
            result_df = calculate_profit_loss(input_file, signal_date_str, evaluation_date_str)
            
            if not result_df.empty:
                # データフレームの内容を確認
                print(f"\n結果の最初の行を確認:\n{result_df.iloc[0]}")
                
                # 結果をCSVファイルに出力
                result_df.to_csv(output_path, index=False, encoding='utf-8')
                print(f"処理完了: {output_filename} に結果を出力しました（{len(result_df)}件）")
                
                # サマリーファイルを作成
                summary_path = generate_summary(result_df, input_file, output_dir)
                print(f"サマリーファイルを出力しました: {os.path.basename(summary_path)}")
            else:
                print(f"警告: {base_filename} の処理結果が空でした")
        except Exception as e:
            print(f"エラー: {input_file} の処理中にエラーが発生しました - {str(e)}")
    
    # 処理時間を表示
    elapsed_time = time.time() - start_time
    print(f"\n処理が完了しました！ 総処理時間: {elapsed_time:.2f}秒")

if __name__ == "__main__":
    main()