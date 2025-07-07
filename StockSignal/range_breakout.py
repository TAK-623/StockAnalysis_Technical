"""
range_breakout.py - レンジ相場をブレイクした銘柄を抽出するモジュール

このモジュールは下記の条件に一致する銘柄を抽出します:
1. 最新のCloseが直近1か月の「前日までの」最高値を更新している
2. 最新の出来高が直近1か月の移動平均の1.5倍よりも多い
3. 出来高が10万以上である
4. 最新のClose値と、High値の差分が、Open値の1.0%未満である（上髭の長い銘柄を除外）
5. ボリンジャーバンドの+2σよりもCloseの値が高い
"""
import os
import pandas as pd
import logging
from typing import List, Dict, Tuple
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
            technical_dir = os.path.join(config.TEST_TECHNICAL_DIR, "StockSignal", "TechnicalSignal")
            result_dir = os.path.join(config.TEST_DIR, "Result")
            company_list_file = config.COMPANY_LIST_TEST_FILE
        else:
            technical_dir = config.TECHNICAL_DIR
            result_dir = os.path.join(config.BASE_DIR, "StockSignal", "Result")
            company_list_file = config.COMPANY_LIST_FILE
        
        # 出力ディレクトリがない場合は作成
        os.makedirs(result_dir, exist_ok=True)
        
        # 企業リストCSVファイルを読み込んで会社名とテーマ情報を取得
        company_info_map = load_company_info_map(is_test_mode)
        
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
                
                print(len(df))
                
                # データが空の場合はスキップ
                if df.empty:
                    logger.warning(f"{csv_file}のデータが空です。スキップします。")
                    continue
                
                # データが十分にない場合はスキップ
                if len(df) < 90:  # 約3か月分のデータ（営業日）が必要
                    logger.warning(f"{csv_file}のデータが不足しています。スキップします。")
                    continue
                
                # 日付列をdatetime型に変換
                df['Date'] = pd.to_datetime(df['Date'])
                
                # 最新の日付を取得
                latest_date = df['Date'].max()
                
                # 3か月前の日付を計算
                three_month_ago = latest_date - timedelta(days=90)
                
                # 3か月分のデータを抽出（最新日を含む）
                three_month_data = df[df['Date'] >= three_month_ago]
                
                # 最新のデータを取得
                latest_data = df.iloc[-1]
                
                # 前日までのデータを抽出（最新日を除く）
                previous_data = three_month_data[three_month_data['Date'] < latest_date]
                
                # 条件1: 最新のCloseが直近1か月の「前日までの」最高値を更新しているか
                if previous_data.empty:
                    # 前日までのデータがない場合は条件を満たさないとみなす
                    condition1 = False
                else:
                    condition1 = latest_data['Close'] >= previous_data['High'].max()
                
                # 条件2: 最新の出来高が直近1か月の移動平均の1.5倍よりも多いか
                volume_ma = three_month_data['Volume'].mean()
                condition2 = latest_data['Volume'] > volume_ma * 1.5  # 移動平均の1.5倍を超えているか
                
                # 条件3: 出来高が10万以上であるか
                condition3 = latest_data['Volume'] >= 100000
                
                # 条件4: Close値が、LowとHighの中間（中央値）よりも高い
                mid_price = (latest_data['High'] + latest_data['Low']) / 2
                condition4 = latest_data['Close'] > mid_price
                
                # 条件4_old: 最新のClose値と、High値の差分が、Open値の1.0%未満である（上髭の長い銘柄を除外）
                high_diff_percent = (latest_data['High'] - latest_data['Close']) / latest_data['Open'] * 100
                # condition4 = high_diff_percent < 1.0
                
                # 条件5: ボリンジャーバンドの+2σよりもCloseの値が高い
                # BB_Upper列が存在し、有効な値があるかチェック
                # if 'BB_Upper' in df.columns and pd.notna(latest_data['BB_Upper']):
                #     condition5 = latest_data['Close'] > latest_data['BB_Upper']
                # else:
                #     # BB_Upper列がない、またはNaNの場合は条件を満たさないとみなす
                #     condition5 = False
                #     logger.warning(f"{csv_file}: ボリンジャーバンド上限値（BB_Upper）が利用できません。")
                
                # デバッグ情報の出力
                ticker = csv_file.split('_')[0]
                logger.debug(f"銘柄: {ticker}")
                logger.debug(f"条件1（前日までの最高値更新）: {condition1}")
                logger.debug(f"最新のClose: {latest_data['Close']}, 前日までの最高値: {previous_data['High'].max() if not previous_data.empty else 'N/A'}")
                logger.debug(f"条件2（出来高1.5倍）: {condition2}")
                logger.debug(f"最新の出来高: {latest_data['Volume']}, 移動平均: {volume_ma}")
                logger.debug(f"条件3（出来高10万以上）: {condition3}")
                logger.debug(f"条件4（HighとLowの中間よりも高値で終了）: {condition4}")
                logger.debug(f"高値と終値の差: {latest_data['High'] - latest_data['Close']}, Open値の1.0%: {latest_data['Open'] * 0.01}, 差分パーセント: {high_diff_percent:.2f}%")
                # logger.debug(f"条件5（BBバンド上抜け）: {condition5}")
                if 'BB_Upper' in df.columns and pd.notna(latest_data['BB_Upper']):
                    logger.debug(f"最新のClose: {latest_data['Close']}, BB上限: {latest_data['BB_Upper']}")
                else:
                    logger.debug(f"BB_Upper値が利用できません")
                
                # すべての条件を満たす場合、結果リストに追加
                # if condition1 and condition2 and condition3 and condition4 and condition5:
                if condition1 and condition2 and condition3 and condition4:
                    # 企業情報を取得（マッピングに存在しない場合は空文字）
                    company_info = company_info_map.get(ticker, {'company': '', 'theme': ''})
                    company_name = company_info.get('company', '')
                    theme = company_info.get('theme', '')
                    
                    # 結果リストに追加
                    breakout_result = {
                        'Ticker': ticker,
                        'Company': company_name,
                        'Theme': theme,
                        'Close': latest_data['Close'],
                        'Previous_High': previous_data['High'].max() if not previous_data.empty else None,
                        'Upper_Shadow_Pct': high_diff_percent
                    }
                    
                    # ボリンジャーバンド情報も追加
                    if 'BB_Upper' in df.columns and pd.notna(latest_data['BB_Upper']):
                        breakout_result['BB_Upper'] = latest_data['BB_Upper']
                    
                    breakout_stocks.append(breakout_result)
                    
                    logger.info(f"レンジブレイク銘柄を検出: {ticker} - {company_name} ({theme})")
                
            except Exception as e:
                logger.error(f"{csv_file}の処理中にエラーが発生しました: {str(e)}")
        
        # 結果をDataFrameに変換
        result_df = pd.DataFrame(breakout_stocks)
        
        # 結果がない場合
        if result_df.empty:
            logger.info("条件に一致する銘柄は見つかりませんでした。")
            # 空のファイルを出力（テーマ列とBB_Upper列を含める）
            result_df = pd.DataFrame(columns=['Ticker', 'Company', 'Theme', 'Close', 'Previous_High', 'Upper_Shadow_Pct', 'BB_Upper'])
        else:
            # データがある場合、テーマ列を日本語に変更し、列の順序を調整
            column_rename = {
                'Theme': 'テーマ',
                'Close': '終値',
                'Previous_High': '前日までの最高値',
                'Upper_Shadow_Pct': '上髭の長さ(%)'
            }
            
            # BB_Upper列がある場合は日本語名を追加
            if 'BB_Upper' in result_df.columns:
                column_rename['BB_Upper'] = 'BB上限(+2σ)'
            
            result_df = result_df.rename(columns=column_rename)
            
            # 終値の表示形式を調整（小数点以下が0の場合は整数表示、それ以外は小数点以下1桁）
            result_df['終値'] = result_df['終値'].apply(
                lambda x: int(x) if x == int(x) else round(x, 1)
            )
            
            # 数値データの小数点以下桁数を調整
            result_df['前日までの最高値'] = result_df['前日までの最高値'].round(2)
            result_df['上髭の長さ(%)'] = result_df['上髭の長さ(%)'].round(2)
            
            # BB上限値がある場合は小数点以下2桁に調整
            if 'BB上限(+2σ)' in result_df.columns:
                result_df['BB上限(+2σ)'] = result_df['BB上限(+2σ)'].round(2)
            
            # 列の順序を調整（Close列の右隣にBB上限列を配置）
            columns_order = ['Ticker', 'Company', 'テーマ', '終値']
            
            # BB上限列がある場合は終値の右隣に配置
            if 'BB上限(+2σ)' in result_df.columns:
                columns_order.append('BB上限(+2σ)')
            
            # 残りの列を追加
            columns_order.extend(['前日までの最高値', '上髭の長さ(%)'])
            
            # 存在する列のみで順序を調整
            available_columns = [col for col in columns_order if col in result_df.columns]
            result_df = result_df[available_columns]
        
        # 結果をCSVに保存
        output_path = os.path.join(result_dir, "Range_Brake.csv")
        result_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        logger.info(f"レンジブレイク銘柄の抽出が完了しました。検出数: {len(result_df)}")
        logger.info(f"結果ファイルの保存先: {output_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"レンジブレイク銘柄の抽出処理中にエラーが発生しました: {str(e)}")
        return False


def load_company_info_map(is_test_mode: bool = False) -> Dict[str, Dict[str, str]]:
    """
    銘柄コードから会社名とテーマへのマッピングを取得します
    
    Args:
        is_test_mode: テストモードかどうか
        
    Returns:
        Dict[str, Dict[str, str]]: 銘柄コードをキー、{'company': 会社名, 'theme': テーマ}を値とする辞書
    """
    # ロガーを取得
    logger = logging.getLogger(__name__)
    # 会社情報マッピング用の空の辞書を初期化
    company_info_map = {}
    
    try:
        # テストモードに応じてCSVファイルのパスを設定
        if is_test_mode:
            # テストモード: テスト用のCSVファイルを使用
            file_path = os.path.join(config.TEST_DIR, config.COMPANY_LIST_TEST_FILE)
        else:
            # 通常モード: 本番用のCSVファイルを使用
            file_path = os.path.join(config.BASE_DIR, config.COMPANY_LIST_FILE)
        
        # CSVファイルを読み込み
        # UTF-8エンコーディングを指定（日本語の会社名を正しく読み込むため）
        df = pd.read_csv(file_path, encoding='utf-8')
        
        # 必要なカラムの確認（Ticker、銘柄名、テーマが必要）
        required_columns = ['Ticker', '銘柄名', 'テーマ']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"企業リストに必要なカラムがありません: {missing_columns}, ファイル: {file_path}")
            # 空のマッピング辞書を返す
            return company_info_map
        
        # マッピングの作成
        # 各行をループして、銘柄コードと会社情報のマッピングを辞書に追加
        for _, row in df.iterrows():
            # 銘柄コードを文字列に変換してキーに（数値が混じる可能性があるため）
            ticker_str = str(row['Ticker'])
            company_info_map[ticker_str] = {
                'company': row['銘柄名'],
                'theme': row['テーマ']
            }
        
        # マッピング作成結果をログに記録
        logger.info(f"{len(company_info_map)}社の会社情報マッピング（会社名・テーマ）を読み込みました")
        
    except Exception as e:
        # 例外発生時はエラーをログに記録
        logger.error(f"会社情報マッピングの読み込み中にエラーが発生しました: {str(e)}")
    
    # 作成されたマッピング辞書を返す（エラー時は空の辞書）
    return company_info_map


# スクリプトが直接実行された場合のテスト用
if __name__ == "__main__":
    # ロガーの設定
    from data_loader import setup_logger
    logger = setup_logger(False)
    
    # 関数のテスト実行
    identify_range_breakouts()