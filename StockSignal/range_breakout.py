"""
range_breakout.py - レンジ相場をブレイクした銘柄を抽出するモジュール

このモジュールは下記の条件に一致する銘柄を抽出します:
1. 最新のCloseが直近1か月の「前日までの」最高値を更新している
2. 最新の出来高が直近1か月の移動平均の1.5倍よりも多い
3. 出来高が10万以上である
4. 最新のClose値と、High値の差分が、Open値の0.5%未満である（上髭の長い銘柄を除外）
"""
import os
import pandas as pd
import logging
from typing import List, Dict
from datetime import datetime, timedelta

# 設定値をインポート
import config
from data_loader import load_company_list

def identify_range_breakouts(is_test_mode: bool = False) -> bool:
    """
    レンジ相場をブレイクした銘柄を抽出する関数
    
    Parameters:
    -----------
    is_test_mode : bool, default=False
        テストモードで実行するかどうか
        
    Returns:
    --------
    bool
        処理が成功したかどうか
    """
    # ロガーの取得
    logger = logging.getLogger(__name__)
    logger.info("レンジブレイク銘柄の抽出処理を開始します...")
    
    try:
        # 入出力ディレクトリの設定（テストモードに応じて切り替え）
        if is_test_mode:
            technical_dir = config.TEST_TECHNICAL_DIR
            result_dir = os.path.join(config.TEST_DIR, "StockSignal", "Result")
            company_list_file = config.COMPANY_LIST_TEST_FILE
        else:
            technical_dir = config.TECHNICAL_DIR
            result_dir = os.path.join(config.BASE_DIR, "StockSignal", "Result")
            company_list_file = config.COMPANY_LIST_FILE
        
        # 出力ディレクトリがない場合は作成
        os.makedirs(result_dir, exist_ok=True)
        
        # 企業リストCSVファイルを読み込む
        company_info = {}
        try:
            # 企業リストファイルのパスを構築
            company_file_path = os.path.join(config.BASE_DIR, company_list_file)
            if is_test_mode:
                company_file_path = os.path.join(config.TEST_DIR, company_list_file)
            
            # CSVファイルを読み込む
            company_df = pd.read_csv(company_file_path)
            
            # Tickerと企業名のマッピングを作成
            # CSVの構造に依存するため、実際のカラム名を使用する必要があります
            # 一般的なCSV構造を想定：Code（証券コード）とName（企業名）のカラムがある
            if 'Code' in company_df.columns and 'Name' in company_df.columns:
                # Code列とName列を使用
                for _, row in company_df.iterrows():
                    # 証券コードを文字列として保持し、必要に応じて左側に0を埋める
                    code = str(row['Code']).strip()
                    # 4桁になるように左側に0を埋める
                    code = code.zfill(4)
                    company_info[code] = row['Name']
            else:
                # 別の列名が使用されている可能性がある場合
                # 最初の列をコード、2番目の列を名前と仮定
                logger.warning("企業リストCSVのカラム名が想定と異なります。最初の2列を使用します。")
                columns = company_df.columns
                if len(columns) >= 2:
                    for _, row in company_df.iterrows():
                        code = str(row[columns[0]]).strip().zfill(4)
                        company_info[code] = row[columns[1]]
                else:
                    logger.error("企業リストCSVの形式が不正です。企業名を取得できません。")
            
            logger.info(f"企業情報を読み込みました。登録数: {len(company_info)}")
            
        except Exception as e:
            logger.error(f"企業リストCSVの読み込み中にエラーが発生しました: {str(e)}")
            logger.warning("企業名なしで処理を続行します。")
        
        # 結果を格納するリスト
        breakout_stocks = []
        
        # テクニカル指標ディレクトリ内のCSVファイルを処理
        csv_files = [f for f in os.listdir(technical_dir) if f.endswith('_signal.csv')]
        
        if not csv_files:
            logger.warning(f"指定されたディレクトリ({technical_dir})にシグナルCSVファイルが見つかりません。")
            return False
        
        # 各銘柄のシグナルファイルを処理
        for csv_file in csv_files:
            try:
                # ファイルパスの作成
                file_path = os.path.join(technical_dir, csv_file)
                
                # CSVファイルの読み込み
                df = pd.read_csv(file_path)
                
                # データが空の場合はスキップ
                if df.empty:
                    logger.warning(f"{csv_file}のデータが空です。スキップします。")
                    continue
                
                # データが十分にない場合はスキップ
                if len(df) < 30:  # 約1か月分のデータ（営業日）が必要
                    logger.warning(f"{csv_file}のデータが不足しています。スキップします。")
                    continue
                
                # 日付列をdatetime型に変換
                df['Date'] = pd.to_datetime(df['Date'])
                
                # 最新の日付を取得
                latest_date = df['Date'].max()
                
                # 1か月前の日付を計算
                one_month_ago = latest_date - timedelta(days=30)
                
                # 1か月分のデータを抽出（最新日を含む）
                one_month_data = df[df['Date'] >= one_month_ago]
                
                # 最新のデータを取得
                latest_data = df.iloc[-1]
                
                # 前日までのデータを抽出（最新日を除く）
                previous_data = one_month_data[one_month_data['Date'] < latest_date]
                
                # 条件1: 最新のCloseが直近1か月の「前日までの」最高値を更新しているか
                if previous_data.empty:
                    # 前日までのデータがない場合は条件を満たさないとみなす
                    condition1 = False
                else:
                    condition1 = latest_data['Close'] >= previous_data['High'].max()
                
                # 条件2: 最新の出来高が直近1か月の移動平均の1.5倍よりも多いか
                volume_ma = one_month_data['Volume'].mean()
                condition2 = latest_data['Volume'] > volume_ma * 1.5  # 移動平均の1.5倍を超えているか
                
                # 条件3: 出来高が10万以上であるか
                condition3 = latest_data['Volume'] >= 100000
                
                # 条件4: 最新のClose値と、High値の差分が、Open値の0.5%未満である（上髭の長い銘柄を除外）
                high_diff_percent = (latest_data['High'] - latest_data['Close']) / latest_data['Open'] * 100
                condition4 = high_diff_percent < 0.5
                
                # デバッグ情報の出力
                ticker = csv_file.split('_')[0]
                logger.debug(f"銘柄: {ticker}")
                logger.debug(f"条件1（前日までの最高値更新）: {condition1}")
                logger.debug(f"最新のClose: {latest_data['Close']}, 前日までの最高値: {previous_data['High'].max() if not previous_data.empty else 'N/A'}")
                logger.debug(f"条件2（出来高1.5倍）: {condition2}")
                logger.debug(f"最新の出来高: {latest_data['Volume']}, 移動平均: {volume_ma}")
                logger.debug(f"条件3（出来高10万以上）: {condition3}")
                logger.debug(f"条件4（上髭の長さ < 0.5%）: {condition4}")
                logger.debug(f"高値と終値の差: {latest_data['High'] - latest_data['Close']}, Open値の0.5%: {latest_data['Open'] * 0.005}, 差分パーセント: {high_diff_percent:.2f}%")
                
                # すべての条件を満たす場合、結果リストに追加
                if condition1 and condition2 and condition3 and condition4:
                    # 企業名を取得（マッピングに存在しない場合は空文字）
                    company_name = company_info.get(ticker, "")
                    
                    # 結果リストに追加
                    breakout_stocks.append({
                        'Ticker': ticker,
                        'Company': company_name,
                        'Close': latest_data['Close'],
                        'Previous_High': previous_data['High'].max() if not previous_data.empty else None,
                        'Upper_Shadow_Pct': high_diff_percent
                    })
                    
                    logger.info(f"レンジブレイク銘柄を検出: {ticker} - {company_name}")
                
            except Exception as e:
                logger.error(f"{csv_file}の処理中にエラーが発生しました: {str(e)}")
        
        # 結果をDataFrameに変換
        result_df = pd.DataFrame(breakout_stocks)
        
        # 結果がない場合
        if result_df.empty:
            logger.info("条件に一致する銘柄は見つかりませんでした。")
            # 空のファイルを出力
            result_df = pd.DataFrame(columns=['Ticker', 'Company', 'Close', 'Previous_High', 'Upper_Shadow_Pct'])
        
        # 結果をCSVに保存
        output_path = os.path.join(result_dir, "Range_Brake.csv")
        result_df.to_csv(output_path, index=False)
        
        logger.info(f"レンジブレイク銘柄の抽出が完了しました。検出数: {len(result_df)}")
        logger.info(f"結果ファイルの保存先: {output_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"レンジブレイク銘柄の抽出処理中にエラーが発生しました: {str(e)}")
        return False

# スクリプトが直接実行された場合のテスト用
if __name__ == "__main__":
    # ロガーの設定
    from data_loader import setup_logger
    logger = setup_logger(False)
    
    # 関数のテスト実行
    identify_range_breakouts()