import pandas as pd
import os
import numpy as np
import logging
import config

def calculate_moving_averages(volume_df, short_term, long_term):
    """
    出来高の移動平均を計算する
    """
    result_data = {}
    
    for industry in volume_df.columns:
        # 業種ごとの出来高データ
        volume_series = volume_df[industry]
        
        # 短期移動平均を計算
        short_ma = volume_series.rolling(window=short_term).mean()
        
        # 長期移動平均を計算
        long_ma = volume_series.rolling(window=long_term).mean()
        
        # 最新の値を取得
        latest_short_ma = short_ma.iloc[-1]
        latest_long_ma = long_ma.iloc[-1]
        
        # 比率を計算（短期MA / 長期MA）
        ratio = latest_short_ma / latest_long_ma if latest_long_ma != 0 else np.nan
        
        # 結果を格納
        result_data[industry] = {
            'Volume': volume_series.iloc[-1],
            'ShortMA': latest_short_ma,
            'LongMA': latest_long_ma,
            'Ratio': ratio,
            'Status': '上回る' if latest_short_ma > latest_long_ma else '下回る'
        }
    
    # 結果をDataFrameに変換
    result_df = pd.DataFrame.from_dict(result_data, orient='index')
    
    return result_df

def save_analysis_results(analysis_df, output_dir, all_file, above_file, below_file):
    """
    分析結果をCSVファイルとして保存する
    """
    # 出力ディレクトリが存在しない場合は作成
    os.makedirs(output_dir, exist_ok=True)
    
    # インデックス名を「業種」に設定
    analysis_df.index.name = '業種'
    
    # 列の順序を変更
    ordered_columns = ['Ratio', 'Volume', 'ShortMA', 'LongMA', 'Status']
    ordered_df = analysis_df[ordered_columns]
    
    # すべての業種の結果を保存
    all_path = os.path.join(output_dir, all_file)
    ordered_df.to_csv(all_path)
    logging.info(f"すべての業種の結果を保存しました: {all_path}")
    
    # 短期MAが長期MAを上回る業種を抽出して保存
    above_df = ordered_df[ordered_df['Status'] == '上回る'].copy()
    above_df = above_df.drop(columns=['Status'])  # Status列を削除
    above_path = os.path.join(output_dir, above_file)
    above_df.to_csv(above_path)
    logging.info(f"短期MAが長期MAを上回る業種を保存しました: {above_path}")
    
    # 短期MAが長期MAを下回る業種を抽出して保存
    below_df = ordered_df[ordered_df['Status'] == '下回る'].copy()
    below_df = below_df.drop(columns=['Status'])  # Status列を削除
    below_path = os.path.join(output_dir, below_file)
    below_df.to_csv(below_path)
    logging.info(f"短期MAが長期MAを下回る業種を保存しました: {below_path}")
    
    return {
        'all': all_path,
        'above': above_path,
        'below': below_path
    }