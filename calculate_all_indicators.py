"""
テクニカル指標の計算処理を提供する専用モジュール
このモジュールでは株価データに対して様々なテクニカル指標（移動平均線、MACD、RSI、RCI、一目均衡表など）を
計算するための関数を提供します。各関数は独立して使用することも、calculate_all_indicators関数を
通じて一括で計算することも可能です。
"""
import numpy as np
import pandas as pd
import talib  # テクニカル分析ライブラリ
import logging
from typing import List, Optional

def calculate_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """
    移動平均線を計算します
    
    Args:
        df: 株価データ（少なくともCloseカラムが必要）
        
    Returns:
        pd.DataFrame: 移動平均線を追加したデータフレーム
    """
    import config  # 設定ファイルから移動平均期間の設定を取得
    
    result = df.copy()  # 元のデータフレームを変更しないようにコピーを作成
    close = df['Close'].values  # 終値の配列を取得
    
    # 設定ファイルで定義された各期間ごとに移動平均を計算
    for period in config.MA_PERIODS:
        # 例: MA5, MA20, MA60など、期間に応じた名前で列を追加
        result[f'MA{period}'] = talib.SMA(close, timeperiod=period)
    
    return result


def calculate_macd(df: pd.DataFrame) -> pd.DataFrame:
    """
    MACDを計算します
    MACD (Moving Average Convergence Divergence) は、短期と長期の指数移動平均線の差を
    示すモメンタム系指標です。
    
    Args:
        df: 株価データ（少なくともCloseカラムが必要）
        
    Returns:
        pd.DataFrame: MACDを追加したデータフレーム（MACD, MACD_Signal, MACD_Histの3カラムが追加される）
    """
    import config  # MACD計算用のパラメータを取得
    
    result = df.copy()  # 元のデータフレームを変更しないようにコピーを作成
    close = df['Close'].values  # 終値の配列を取得
    
    # MACD, MACD Signal, MACD Hist を計算
    # - MACD: 短期EMAと長期EMAの差
    # - MACD_Signal: MACDの指数移動平均
    # - MACD_Hist: MACDとSignalの差（ヒストグラム）
    macd, macd_signal, macd_hist = talib.MACD(
        close, 
        fastperiod=config.MACD_FAST_PERIOD,  # 短期期間（標準: 12日）
        slowperiod=config.MACD_SLOW_PERIOD,  # 長期期間（標準: 26日）
        signalperiod=config.MACD_SIGNAL_PERIOD  # シグナル期間（標準: 9日）
    )
    
    # 計算結果をデータフレームに追加
    result['MACD'] = macd
    result['MACD_Signal'] = macd_signal
    result['MACD_Hist'] = macd_hist
    
    return result


def calculate_rsi(df: pd.DataFrame) -> pd.DataFrame:
    """
    短期と長期のRSIを計算します
    RSI (Relative Strength Index) は、価格の上昇と下落の大きさを比較して、
    買われすぎ・売られすぎを判断するための指標です。
    
    Args:
        df: 株価データ（少なくともCloseカラムが必要）
        
    Returns:
        pd.DataFrame: RSIを追加したデータフレーム（短期RSI、長期RSI、標準RSIのカラムが追加される）
    """
    import config  # RSI計算用のパラメータを取得
    
    result = df.copy()  # 元のデータフレームを変更しないようにコピーを作成
    close = df['Close'].values  # 終値の配列を取得
    
    # 短期RSIを計算（例：9日）
    # 短期間のRSIは市場の短期的な過熱感や底入れを検出するのに有効
    result[f'RSI{config.RSI_SHORT_PERIOD}'] = talib.RSI(close, timeperiod=config.RSI_SHORT_PERIOD)
    
    # 長期RSIを計算（例：14日）
    # 長期間のRSIは中長期的なトレンドの強さを測定するのに有効
    result[f'RSI{config.RSI_LONG_PERIOD}'] = talib.RSI(close, timeperiod=config.RSI_LONG_PERIOD)
    
    # 後方互換性のために元のRSIカラムも維持（長期RSIと同じ値）
    # 既存のコードやシステムとの互換性を保つため
    result['RSI'] = result[f'RSI{config.RSI_LONG_PERIOD}']
    
    return result


def calculate_rci(df: pd.DataFrame) -> pd.DataFrame:
    """
    短期と長期のRCI（Rank Correlation Index）を計算します
    RCIは価格変動の順位相関を利用して、トレンドの転換点を予測する指標です。
    
    Args:
        df: 株価データ（少なくともCloseカラムが必要）
        
    Returns:
        pd.DataFrame: RCIを追加したデータフレーム（短期RCI、長期RCI、関連指標が追加される）
    """
    import config  # RCI計算用のパラメータを取得
    
    result = df.copy()  # 元のデータフレームを変更しないようにコピーを作成
    close = df['Close'].values  # 終値の配列を取得
    data_length = len(close)  # データの長さを取得
    
    # 短期RCIの計算用の配列を初期化（NaNで埋める）
    rci_short = np.full(data_length, np.nan)
    short_period = config.RCI_SHORT_PERIOD  # 短期期間（例：9日）
    
    # 長期RCIの計算用の配列を初期化（NaNで埋める）
    rci_long = np.full(data_length, np.nan)
    long_period = config.RCI_LONG_PERIOD  # 長期期間（例：26日）
    
    # RCIの計算関数 - スピアマンの順位相関係数を使用
    def compute_rci(period, i):
        # 十分なデータが無い場合はNaNを返す
        if i < period - 1:
            return np.nan
            
        # 指定期間の価格データを取得
        price_window = close[i-period+1:i+1]
        
        # 時系列の順位を生成（最新が1）- 時間的な順番を表す
        time_ranks = np.arange(1, period + 1)
        
        # 価格の順位を計算（高い方が1）
        # np.argsortがインデックスを返し、それを逆順にしてインデックス1から始める
        price_ranks = period - np.argsort(np.argsort(-price_window)) 
        
        # 時系列と価格順位の差の二乗和
        d_squared = np.sum((time_ranks - price_ranks) ** 2)
        
        # RCI計算式: スピアマンの順位相関係数を百分率で表示
        # 100に近いほど上昇トレンド、-100に近いほど下降トレンド
        rci_value = (1 - 6 * d_squared / (period * (period**2 - 1))) * 100
        
        return rci_value
    
    # 各日付でRCIを計算
    for i in range(data_length):
        # 短期RCIの計算（データが十分にある場合）
        if i >= short_period - 1:
            rci_short[i] = compute_rci(short_period, i)
        
        # 長期RCIの計算（データが十分にある場合）
        if i >= long_period - 1:
            rci_long[i] = compute_rci(long_period, i)
    
    # 結果をデータフレームに追加
    result[f'RCI{short_period}'] = rci_short
    result[f'RCI{long_period}'] = rci_long
    
    # RCIの状態を判定（買われすぎ/売られすぎの基準は±80）
    # RCIが80以上: 強い上昇トレンド（買われすぎの可能性）
    result['RCI_Short_Overbought'] = result[f'RCI{short_period}'] > 80
    # RCIが-80以下: 強い下降トレンド（売られすぎの可能性）
    result['RCI_Short_Oversold'] = result[f'RCI{short_period}'] < -80
    result['RCI_Long_Overbought'] = result[f'RCI{long_period}'] > 80
    result['RCI_Long_Oversold'] = result[f'RCI{long_period}'] < -80
    
    return result


def calculate_ichimoku(df: pd.DataFrame) -> pd.DataFrame:
    """
    一目均衡表を計算します（shiftを使わない安全な実装）
    一目均衡表は、トレンドの方向、勢い、支持/抵抗水準、およびシグナルを判断するための
    複合的なテクニカル分析ツールです。
    
    Args:
        df: 株価データ（High, Low, Closeカラムが必要）
        
    Returns:
        pd.DataFrame: 一目均衡表のデータを追加したデータフレーム
    """
    import config  # 一目均衡表のパラメータを取得
    
    result = df.copy()  # 元のデータフレームを変更しないようにコピーを作成
    
    # パラメータの取得
    tenkan_period = config.ICHIMOKU_TENKAN_PERIOD  # 転換線期間（通常9日）
    kijun_period = config.ICHIMOKU_KIJUN_PERIOD    # 基準線期間（通常26日）
    senkou_span_b_period = config.ICHIMOKU_SENKOU_SPAN_B_PERIOD  # 先行スパンB期間（通常52日）
    displacement = config.ICHIMOKU_DISPLACEMENT    # 先行スパン先行期間（通常26日）
    
    # 配列を直接操作するために、データをNumPy配列として取得
    high_values = df['High'].values   # 高値
    low_values = df['Low'].values     # 安値
    close_values = df['Close'].values  # 終値
    
    # データ長
    data_length = len(high_values)
    
    # 転換線（Tenkan-sen）- (n日間の高値 + n日間の安値) / 2
    # 短期的な価格変動のバランスを示す
    tenkan_sen = np.full(data_length, np.nan)
    
    for i in range(tenkan_period - 1, data_length):
        period_high = np.max(high_values[i - tenkan_period + 1:i + 1])  # 期間内の最高値
        period_low = np.min(low_values[i - tenkan_period + 1:i + 1])    # 期間内の最安値
        tenkan_sen[i] = (period_high + period_low) / 2  # 中値を計算
    
    result['Ichimoku_Tenkan'] = tenkan_sen
    
    # 基準線（Kijun-sen）- (n日間の高値 + n日間の安値) / 2
    # 中期的な価格変動のバランスを示す
    kijun_sen = np.full(data_length, np.nan)
    
    for i in range(kijun_period - 1, data_length):
        period_high = np.max(high_values[i - kijun_period + 1:i + 1])  # 期間内の最高値
        period_low = np.min(low_values[i - kijun_period + 1:i + 1])    # 期間内の最安値
        kijun_sen[i] = (period_high + period_low) / 2  # 中値を計算
    
    result['Ichimoku_Kijun'] = kijun_sen
    
    # 先行スパンA（Senkou Span A）- (転換線 + 基準線) / 2を26日先行
    # 雲の上側の境界線を形成
    senkou_span_a = np.full(data_length, np.nan)
    
    for i in range(tenkan_period - 1, data_length):
        # 26日後のインデックスが存在する場合のみ計算
        if i + displacement < data_length:
            senkou_span_a[i + displacement] = (tenkan_sen[i] + kijun_sen[i]) / 2
    
    result['Ichimoku_SenkouA'] = senkou_span_a
    
    # 先行スパンB（Senkou Span B）- (n日間の高値 + n日間の安値) / 2を26日先行
    # 雲の下側の境界線を形成
    senkou_span_b = np.full(data_length, np.nan)
    
    for i in range(senkou_span_b_period - 1, data_length):
        period_high = np.max(high_values[i - senkou_span_b_period + 1:i + 1])  # 期間内の最高値
        period_low = np.min(low_values[i - senkou_span_b_period + 1:i + 1])    # 期間内の最安値
        # 26日後のインデックスが存在する場合のみ計算
        if i + displacement < data_length:
            senkou_span_b[i + displacement] = (period_high + period_low) / 2
    
    result['Ichimoku_SenkouB'] = senkou_span_b
    
    # 遅行スパン（Chikou Span）- 現在の終値を26日前に表示
    # 価格と過去の関係を示す
    chikou_span = np.full(data_length, np.nan)
    
    for i in range(displacement, data_length):
        chikou_span[i - displacement] = close_values[i]
    
    result['Ichimoku_Chikou'] = chikou_span
    
    # 雲の判定 - 価格と雲の位置関係
    # 雲の上: 強気市場の可能性、雲の下: 弱気市場の可能性、雲の中: トレンド不明瞭
    result['Ichimoku_Above_Cloud'] = False  # 価格が雲の上にある
    result['Ichimoku_Below_Cloud'] = False  # 価格が雲の下にある
    result['Ichimoku_In_Cloud'] = False     # 価格が雲の中にある
    
    for i in range(data_length):
        # 先行スパンA、Bが両方とも計算されている場合のみ判定
        if not (np.isnan(senkou_span_a[i]) or np.isnan(senkou_span_b[i])):
            max_cloud = max(senkou_span_a[i], senkou_span_b[i])  # 雲の上端
            min_cloud = min(senkou_span_a[i], senkou_span_b[i])  # 雲の下端
            
            # 価格が雲の上にあるか判定
            if close_values[i] > max_cloud:
                result.loc[df.index[i], 'Ichimoku_Above_Cloud'] = True
            # 価格が雲の下にあるか判定
            elif close_values[i] < min_cloud:
                result.loc[df.index[i], 'Ichimoku_Below_Cloud'] = True
            # 価格が雲の中にあるか判定
            else:
                result.loc[df.index[i], 'Ichimoku_In_Cloud'] = True
    
    # 雲の状態（文字列表現）- 日本語表記で状態を記録
    result['Ichimoku_Cloud_Status'] = ''
    for i in range(data_length):
        if result.iloc[i]['Ichimoku_Above_Cloud']:
            result.iloc[i, result.columns.get_indexer(['Ichimoku_Cloud_Status'])[0]] = '雲の上'
        elif result.iloc[i]['Ichimoku_Below_Cloud']:
            result.iloc[i, result.columns.get_indexer(['Ichimoku_Cloud_Status'])[0]] = '雲の下'
        elif result.iloc[i]['Ichimoku_In_Cloud']:
            result.iloc[i, result.columns.get_indexer(['Ichimoku_Cloud_Status'])[0]] = '雲の中'
    
    # 遅行線の判定 - 遅行線と価格の位置関係
    # 遅行線が価格より上: 上昇トレンドの可能性、下: 下降トレンドの可能性
    result['Ichimoku_Chikou_Above_Price'] = False  # 遅行線が価格より上
    result['Ichimoku_Chikou_Below_Price'] = False  # 遅行線が価格より下
    
    for i in range(data_length - displacement):
        # 遅行線が計算されている場合のみ判定
        if not np.isnan(chikou_span[i]):
            price_at_chikou_time = close_values[i]  # 遅行線に対応する時点の価格
            # 遅行線が価格より上にあるか判定
            if chikou_span[i] > price_at_chikou_time:
                result.iloc[i + displacement, result.columns.get_indexer(['Ichimoku_Chikou_Above_Price'])[0]] = True
            # 遅行線が価格より下にあるか判定
            elif chikou_span[i] < price_at_chikou_time:
                result.iloc[i + displacement, result.columns.get_indexer(['Ichimoku_Chikou_Below_Price'])[0]] = True
    
    # 転換線と基準線の位置関係
    # 転換線が基準線より上: 短期的上昇の可能性、下: 短期的下降の可能性
    result['Ichimoku_Tenkan_Above_Kijun'] = False  # 転換線が基準線より上
    result['Ichimoku_Tenkan_Below_Kijun'] = False  # 転換線が基準線より下
    
    for i in range(data_length):
        # 転換線と基準線が両方とも計算されている場合のみ判定
        if not (np.isnan(tenkan_sen[i]) or np.isnan(kijun_sen[i])):
            # 転換線が基準線より上にあるか判定
            if tenkan_sen[i] > kijun_sen[i]:
                result.iloc[i, result.columns.get_indexer(['Ichimoku_Tenkan_Above_Kijun'])[0]] = True
            # 転換線が基準線より下にあるか判定
            elif tenkan_sen[i] < kijun_sen[i]:
                result.iloc[i, result.columns.get_indexer(['Ichimoku_Tenkan_Below_Kijun'])[0]] = True
    
    # 三役好転・三役暗転の基本条件
    # 三役好転: 上昇トレンドへの転換を示す複合シグナル
    # 三役暗転: 下降トレンドへの転換を示す複合シグナル
    result['Ichimoku_Sanryaku_Koten'] = False  # 三役好転の基本条件
    result['Ichimoku_Sanryaku_Anten'] = False  # 三役暗転の基本条件
    
    for i in range(data_length):
        # 各指標が計算されている場合のみ判定
        if (not np.isnan(tenkan_sen[i]) and not np.isnan(kijun_sen[i]) and 
            i < data_length and not pd.isna(result.iloc[i]['Ichimoku_Above_Cloud']) and 
            not pd.isna(result.iloc[i]['Ichimoku_Chikou_Above_Price']) and 
            not pd.isna(result.iloc[i]['Ichimoku_Tenkan_Above_Kijun'])):
            
            # 三役好転の基本条件：
            # 1. 価格が雲の上
            # 2. 遅行線が価格より上
            # 3. 転換線が基準線より上
            result.iloc[i, result.columns.get_indexer(['Ichimoku_Sanryaku_Koten'])[0]] = (
                result.iloc[i]['Ichimoku_Above_Cloud'] and 
                result.iloc[i]['Ichimoku_Chikou_Above_Price'] and 
                result.iloc[i]['Ichimoku_Tenkan_Above_Kijun']
            )
            
            # 三役暗転の基本条件：
            # 1. 価格が雲の下
            # 2. 遅行線が価格より下
            # 3. 転換線が基準線より下
            result.iloc[i, result.columns.get_indexer(['Ichimoku_Sanryaku_Anten'])[0]] = (
                result.iloc[i]['Ichimoku_Below_Cloud'] and 
                result.iloc[i]['Ichimoku_Chikou_Below_Price'] and 
                result.iloc[i]['Ichimoku_Tenkan_Below_Kijun']
            )
    
    # 三役好転・三役暗転の判定（トレンド転換）
    # 三役好転・三役暗転は前日と今日のデータを比較して判定する
    result['Ichimoku_SanYaku'] = ''  # 三役判定結果を格納
    
    # 前日と今日のデータを使用して判定するため、2行以上のデータが必要
    if data_length >= 2:
        for i in range(1, data_length):
            # 転換線または基準線が計算されていない場合はスキップ
            if (np.isnan(tenkan_sen[i-1]) or np.isnan(kijun_sen[i-1]) or 
                np.isnan(tenkan_sen[i]) or np.isnan(kijun_sen[i])):
                continue
            
            # 転換線が基準線を上抜けたか判定（前日: 転換線 <= 基準線、当日: 転換線 > 基準線）
            tenkan_uenuke = tenkan_sen[i-1] <= kijun_sen[i-1] and tenkan_sen[i] > kijun_sen[i]
            
            # 転換線が基準線を下抜けたか判定（前日: 転換線 >= 基準線、当日: 転換線 < 基準線）
            tenkan_shitanuke = tenkan_sen[i-1] >= kijun_sen[i-1] and tenkan_sen[i] < kijun_sen[i]
            
            # 三役好転: 転換線が基準線を上抜け + 基本条件満たす
            if tenkan_uenuke and result.iloc[i]['Ichimoku_Sanryaku_Koten']:
                result.iloc[i, result.columns.get_indexer(['Ichimoku_SanYaku'])[0]] = '三役好転'
            
            # 三役暗転: 転換線が基準線を下抜け + 基本条件満たす
            elif tenkan_shitanuke and result.iloc[i]['Ichimoku_Sanryaku_Anten']:
                result.iloc[i, result.columns.get_indexer(['Ichimoku_SanYaku'])[0]] = '三役暗転'
    
    return result


def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    すべてのテクニカル指標を計算します
    このメイン関数は、各テクニカル指標計算関数を順番に呼び出して、
    データフレームに全ての指標を追加します。
    
    Args:
        df: 株価データ (OHLCV形式が望ましい)
        
    Returns:
        pd.DataFrame: すべてのテクニカル指標を追加したデータフレーム
    """
    result = df.copy()  # 元のデータフレームを変更しないようにコピーを作成
    
    # 移動平均線の計算
    # MA5, MA20, MA60などの各期間の移動平均線を追加
    result = calculate_moving_averages(result)
    
    # MACDの計算
    # MACD, MACD_Signal, MACD_Histを追加
    result = calculate_macd(result)
    
    # RSIの計算
    # 短期RSI、長期RSI、標準RSIを追加
    result = calculate_rsi(result)
    
    # RCIの計算
    # 短期RCI、長期RCI、および関連する状態判定を追加
    result = calculate_rci(result)
    
    # 一目均衡表の計算
    # 転換線、基準線、先行スパンA/B、遅行線、各種判定結果を追加
    result = calculate_ichimoku(result)
    
    return result