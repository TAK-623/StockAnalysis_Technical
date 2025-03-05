"""
テクニカル指標の計算処理を提供する専用モジュール
"""
import numpy as np
import pandas as pd
import talib
import logging
from typing import List, Optional

def calculate_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """
    移動平均線を計算します
    
    Args:
        df: 株価データ
        
    Returns:
        pd.DataFrame: 移動平均線を追加したデータフレーム
    """
    import config
    
    result = df.copy()
    close = df['Close'].values
    
    for period in config.MA_PERIODS:
        result[f'MA{period}'] = talib.SMA(close, timeperiod=period)
    
    return result


def calculate_macd(df: pd.DataFrame) -> pd.DataFrame:
    """
    MACDを計算します
    
    Args:
        df: 株価データ
        
    Returns:
        pd.DataFrame: MACDを追加したデータフレーム
    """
    import config
    
    result = df.copy()
    close = df['Close'].values
    
    # MACD, MACD Signal, MACD Hist を計算
    macd, macd_signal, macd_hist = talib.MACD(
        close, 
        fastperiod=config.MACD_FAST_PERIOD, 
        slowperiod=config.MACD_SLOW_PERIOD, 
        signalperiod=config.MACD_SIGNAL_PERIOD
    )
    
    result['MACD'] = macd
    result['MACD_Signal'] = macd_signal
    result['MACD_Hist'] = macd_hist
    
    return result


def calculate_rsi(df: pd.DataFrame) -> pd.DataFrame:
    """
    短期と長期のRSIを計算します
    
    Args:
        df: 株価データ
        
    Returns:
        pd.DataFrame: RSIを追加したデータフレーム
    """
    import config
    
    result = df.copy()
    close = df['Close'].values
    
    # 短期RSIを計算
    result[f'RSI{config.RSI_SHORT_PERIOD}'] = talib.RSI(close, timeperiod=config.RSI_SHORT_PERIOD)
    
    # 長期RSIを計算
    result[f'RSI{config.RSI_LONG_PERIOD}'] = talib.RSI(close, timeperiod=config.RSI_LONG_PERIOD)
    
    # 後方互換性のために元のRSIカラムも維持
    result['RSI'] = result[f'RSI{config.RSI_LONG_PERIOD}']
    
    return result


def calculate_rci(df: pd.DataFrame) -> pd.DataFrame:
    """
    短期と長期のRCI（Rank Correlation Index）を計算します
    
    Args:
        df: 株価データ
        
    Returns:
        pd.DataFrame: RCIを追加したデータフレーム
    """
    import config
    
    result = df.copy()
    close = df['Close'].values
    data_length = len(close)
    
    # 短期RCIの計算
    rci_short = np.full(data_length, np.nan)
    short_period = config.RCI_SHORT_PERIOD
    
    # 長期RCIの計算
    rci_long = np.full(data_length, np.nan)
    long_period = config.RCI_LONG_PERIOD
    
    # RCIの計算関数
    def compute_rci(period, i):
        if i < period - 1:
            return np.nan
            
        # 指定期間の価格データを取得
        price_window = close[i-period+1:i+1]
        
        # 時系列の順位を生成（最新が1）
        time_ranks = np.arange(1, period + 1)
        
        # 価格の順位を計算（高い方が1）
        # np.argsortがインデックスを返し、それを逆順にしてインデックス1から始める
        price_ranks = period - np.argsort(np.argsort(-price_window)) 
        
        # 時系列と価格順位の差の二乗和
        d_squared = np.sum((time_ranks - price_ranks) ** 2)
        
        # RCI計算式
        rci_value = (1 - 6 * d_squared / (period * (period**2 - 1))) * 100
        
        return rci_value
    
    # 各日付でRCIを計算
    for i in range(data_length):
        if i >= short_period - 1:
            rci_short[i] = compute_rci(short_period, i)
        
        if i >= long_period - 1:
            rci_long[i] = compute_rci(long_period, i)
    
    # 結果をデータフレームに追加
    result[f'RCI{short_period}'] = rci_short
    result[f'RCI{long_period}'] = rci_long
    
    # RCIの状態を判定
    result['RCI_Short_Overbought'] = result[f'RCI{short_period}'] > 80
    result['RCI_Short_Oversold'] = result[f'RCI{short_period}'] < -80
    result['RCI_Long_Overbought'] = result[f'RCI{long_period}'] > 80
    result['RCI_Long_Oversold'] = result[f'RCI{long_period}'] < -80
    
    return result


def calculate_ichimoku(df: pd.DataFrame) -> pd.DataFrame:
    """
    一目均衡表を計算します（shiftを使わない安全な実装）
    
    Args:
        df: 株価データ
        
    Returns:
        pd.DataFrame: 一目均衡表のデータを追加したデータフレーム
    """
    import config
    
    result = df.copy()
    
    # パラメータの取得
    tenkan_period = config.ICHIMOKU_TENKAN_PERIOD
    kijun_period = config.ICHIMOKU_KIJUN_PERIOD
    senkou_span_b_period = config.ICHIMOKU_SENKOU_SPAN_B_PERIOD
    displacement = config.ICHIMOKU_DISPLACEMENT
    
    # 配列を直接操作するために、データをNumPy配列として取得
    high_values = df['High'].values
    low_values = df['Low'].values
    close_values = df['Close'].values
    
    # データ長
    data_length = len(high_values)
    
    # 転換線（Tenkan-sen）- (n日間の高値 + n日間の安値) / 2
    tenkan_sen = np.full(data_length, np.nan)
    
    for i in range(tenkan_period - 1, data_length):
        period_high = np.max(high_values[i - tenkan_period + 1:i + 1])
        period_low = np.min(low_values[i - tenkan_period + 1:i + 1])
        tenkan_sen[i] = (period_high + period_low) / 2
    
    result['Ichimoku_Tenkan'] = tenkan_sen
    
    # 基準線（Kijun-sen）- (n日間の高値 + n日間の安値) / 2
    kijun_sen = np.full(data_length, np.nan)
    
    for i in range(kijun_period - 1, data_length):
        period_high = np.max(high_values[i - kijun_period + 1:i + 1])
        period_low = np.min(low_values[i - kijun_period + 1:i + 1])
        kijun_sen[i] = (period_high + period_low) / 2
    
    result['Ichimoku_Kijun'] = kijun_sen
    
    # 先行スパンA（Senkou Span A）- (転換線 + 基準線) / 2を26日先行
    senkou_span_a = np.full(data_length, np.nan)
    
    for i in range(tenkan_period - 1, data_length):
        if i + displacement < data_length:
            senkou_span_a[i + displacement] = (tenkan_sen[i] + kijun_sen[i]) / 2
    
    result['Ichimoku_SenkouA'] = senkou_span_a
    
    # 先行スパンB（Senkou Span B）- (n日間の高値 + n日間の安値) / 2を26日先行
    senkou_span_b = np.full(data_length, np.nan)
    
    for i in range(senkou_span_b_period - 1, data_length):
        period_high = np.max(high_values[i - senkou_span_b_period + 1:i + 1])
        period_low = np.min(low_values[i - senkou_span_b_period + 1:i + 1])
        if i + displacement < data_length:
            senkou_span_b[i + displacement] = (period_high + period_low) / 2
    
    result['Ichimoku_SenkouB'] = senkou_span_b
    
    # 遅行スパン（Chikou Span）- 現在の終値を26日前に表示
    chikou_span = np.full(data_length, np.nan)
    
    for i in range(displacement, data_length):
        chikou_span[i - displacement] = close_values[i]
    
    result['Ichimoku_Chikou'] = chikou_span
    
    # 雲の判定 - 価格と雲の位置関係
    result['Ichimoku_Above_Cloud'] = False
    result['Ichimoku_Below_Cloud'] = False
    result['Ichimoku_In_Cloud'] = False
    
    for i in range(data_length):
        if not (np.isnan(senkou_span_a[i]) or np.isnan(senkou_span_b[i])):
            max_cloud = max(senkou_span_a[i], senkou_span_b[i])
            min_cloud = min(senkou_span_a[i], senkou_span_b[i])
            
            if close_values[i] > max_cloud:
                result.loc[df.index[i], 'Ichimoku_Above_Cloud'] = True
            elif close_values[i] < min_cloud:
                result.loc[df.index[i], 'Ichimoku_Below_Cloud'] = True
            else:
                result.loc[df.index[i], 'Ichimoku_In_Cloud'] = True
    
    # 雲の状態（文字列表現）
    result['Ichimoku_Cloud_Status'] = ''
    for i in range(data_length):
        if result.iloc[i]['Ichimoku_Above_Cloud']:
            result.iloc[i, result.columns.get_indexer(['Ichimoku_Cloud_Status'])[0]] = '雲の上'
        elif result.iloc[i]['Ichimoku_Below_Cloud']:
            result.iloc[i, result.columns.get_indexer(['Ichimoku_Cloud_Status'])[0]] = '雲の下'
        elif result.iloc[i]['Ichimoku_In_Cloud']:
            result.iloc[i, result.columns.get_indexer(['Ichimoku_Cloud_Status'])[0]] = '雲の中'
    
    # 遅行線の判定 - 遅行線と価格の位置関係
    result['Ichimoku_Chikou_Above_Price'] = False
    result['Ichimoku_Chikou_Below_Price'] = False
    
    for i in range(data_length - displacement):
        if not np.isnan(chikou_span[i]):
            price_at_chikou_time = close_values[i]
            if chikou_span[i] > price_at_chikou_time:
                result.iloc[i + displacement, result.columns.get_indexer(['Ichimoku_Chikou_Above_Price'])[0]] = True
            elif chikou_span[i] < price_at_chikou_time:
                result.iloc[i + displacement, result.columns.get_indexer(['Ichimoku_Chikou_Below_Price'])[0]] = True
    
    # 転換線と基準線の位置関係
    result['Ichimoku_Tenkan_Above_Kijun'] = False
    result['Ichimoku_Tenkan_Below_Kijun'] = False
    
    for i in range(data_length):
        if not (np.isnan(tenkan_sen[i]) or np.isnan(kijun_sen[i])):
            if tenkan_sen[i] > kijun_sen[i]:
                result.iloc[i, result.columns.get_indexer(['Ichimoku_Tenkan_Above_Kijun'])[0]] = True
            elif tenkan_sen[i] < kijun_sen[i]:
                result.iloc[i, result.columns.get_indexer(['Ichimoku_Tenkan_Below_Kijun'])[0]] = True
    
    # 三役好転・三役暗転の基本条件
    result['Ichimoku_Sanryaku_Koten'] = False
    result['Ichimoku_Sanryaku_Anten'] = False
    
    for i in range(data_length):
        if (not np.isnan(tenkan_sen[i]) and not np.isnan(kijun_sen[i]) and 
            i < data_length and not pd.isna(result.iloc[i]['Ichimoku_Above_Cloud']) and 
            not pd.isna(result.iloc[i]['Ichimoku_Chikou_Above_Price']) and 
            not pd.isna(result.iloc[i]['Ichimoku_Tenkan_Above_Kijun'])):
            
            result.iloc[i, result.columns.get_indexer(['Ichimoku_Sanryaku_Koten'])[0]] = (
                result.iloc[i]['Ichimoku_Above_Cloud'] and 
                result.iloc[i]['Ichimoku_Chikou_Above_Price'] and 
                result.iloc[i]['Ichimoku_Tenkan_Above_Kijun']
            )
            
            result.iloc[i, result.columns.get_indexer(['Ichimoku_Sanryaku_Anten'])[0]] = (
                result.iloc[i]['Ichimoku_Below_Cloud'] and 
                result.iloc[i]['Ichimoku_Chikou_Below_Price'] and 
                result.iloc[i]['Ichimoku_Tenkan_Below_Kijun']
            )
    
    # 三役好転・三役暗転の判定（トレンド転換）
    result['Ichimoku_SanYaku'] = ''
    
    # 前日と今日のデータを使用して判定するため、2行以上のデータが必要
    if data_length >= 2:
        for i in range(1, data_length):
            if (np.isnan(tenkan_sen[i-1]) or np.isnan(kijun_sen[i-1]) or 
                np.isnan(tenkan_sen[i]) or np.isnan(kijun_sen[i])):
                continue
            
            # 転換線が基準線を上抜けたか判定
            tenkan_uenuke = tenkan_sen[i-1] <= kijun_sen[i-1] and tenkan_sen[i] > kijun_sen[i]
            
            # 転換線が基準線を下抜けたか判定
            tenkan_shitanuke = tenkan_sen[i-1] >= kijun_sen[i-1] and tenkan_sen[i] < kijun_sen[i]
            
            # 三役好転: 転換線が基準線を上抜け + 基本条件
            if tenkan_uenuke and result.iloc[i]['Ichimoku_Sanryaku_Koten']:
                result.iloc[i, result.columns.get_indexer(['Ichimoku_SanYaku'])[0]] = '三役好転'
            
            # 三役暗転: 転換線が基準線を下抜け + 基本条件
            elif tenkan_shitanuke and result.iloc[i]['Ichimoku_Sanryaku_Anten']:
                result.iloc[i, result.columns.get_indexer(['Ichimoku_SanYaku'])[0]] = '三役暗転'
    
    return result


def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    すべてのテクニカル指標を計算します
    
    Args:
        df: 株価データ
        
    Returns:
        pd.DataFrame: テクニカル指標を追加したデータフレーム
    """
    result = df.copy()
    
    # 移動平均線
    result = calculate_moving_averages(result)
    
    # MACD
    result = calculate_macd(result)
    
    # RSI
    result = calculate_rsi(result)
    
    # RCI
    result = calculate_rci(result)
    
    # 一目均衡表
    result = calculate_ichimoku(result)
    
    return result