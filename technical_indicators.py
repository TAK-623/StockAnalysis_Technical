"""
テクニカル指標計算モジュール - 株価データから各種テクニカル指標を計算します
TALibを使用して計算を行います

このモジュールは、株価データから様々なテクニカル指標を計算し、売買シグナルを生成します。
各テクニカル指標の計算関数と、それらを組み合わせて売買判断を行う機能を提供しています。
また、複数銘柄の一括処理や結果の保存機能も備えています。
"""
import os
import pandas as pd
import numpy as np
import talib  # テクニカル分析用ライブラリ
import logging
from typing import List, Dict, Optional, Union, Tuple


def calculate_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """
    移動平均線を計算します
    
    config.MA_PERIODSで指定された期間の単純移動平均線（SMA）を計算します。
    移動平均線はトレンドの方向性や強さを確認するための基本的な指標です。
    
    Args:
        df: 株価データ（少なくともCloseカラムが必要）
        
    Returns:
        pd.DataFrame: 移動平均線を追加したデータフレーム（MA5, MA25, MA75など）
    """
    import config
    
    # 元のデータを変更しないようにコピーを作成
    result = df.copy()
    # 終値の配列を取得
    close = df['Close'].values
    
    # 設定された各期間の移動平均線を計算
    for period in config.MA_PERIODS:
        # 例: MA5, MA25, MA75などのカラム名で各期間の移動平均を計算
        result[f'MA{period}'] = talib.SMA(close, timeperiod=period)
    
    return result


def calculate_macd(df: pd.DataFrame) -> pd.DataFrame:
    """
    MACDを計算します
    
    MACD（Moving Average Convergence Divergence）は2つの指数移動平均線の差を
    示すモメンタム指標です。短期EMA - 長期EMAの値とそのシグナル線、
    およびヒストグラムを計算します。
    
    Args:
        df: 株価データ（少なくともCloseカラムが必要）
        
    Returns:
        pd.DataFrame: MACDを追加したデータフレーム（MACD, MACD_Signal, MACD_Histの3カラム）
    """
    import config
    
    # 元のデータを変更しないようにコピーを作成
    result = df.copy()
    # 終値の配列を取得
    close = df['Close'].values
    
    # MACD, MACD Signal, MACD Hist を計算
    # - MACD：短期EMAと長期EMAの差
    # - MACD_Signal：MACDの指数移動平均
    # - MACD_Hist：MACDとシグナル線の差（ヒストグラム）
    macd, macd_signal, macd_hist = talib.MACD(
        close, 
        fastperiod=config.MACD_FAST_PERIOD,  # 短期期間（通常：12日）
        slowperiod=config.MACD_SLOW_PERIOD,  # 長期期間（通常：26日）
        signalperiod=config.MACD_SIGNAL_PERIOD  # シグナル期間（通常：9日）
    )
    
    # 計算結果をデータフレームに追加
    result['MACD'] = macd
    result['MACD_Signal'] = macd_signal
    result['MACD_Hist'] = macd_hist
    
    return result


def calculate_rsi(df: pd.DataFrame) -> pd.DataFrame:
    """
    短期と長期のRSIを計算します
    
    RSI（Relative Strength Index）は、過去の価格変動の強弱を0～100の
    範囲で数値化した指標です。一般的に70以上で買われすぎ、30以下で
    売られすぎとされます。短期と長期の2種類のRSIを計算します。
    
    Args:
        df: 株価データ（少なくともCloseカラムが必要）
        
    Returns:
        pd.DataFrame: RSIを追加したデータフレーム（短期RSI、長期RSI、標準RSIのカラム）
    """
    import config
    
    # 元のデータを変更しないようにコピーを作成
    result = df.copy()
    # 終値の配列を取得
    close = df['Close'].values
    
    # 短期RSIを計算（例：9日）
    # 市場の短期的な過熱感や底入れを検出するのに有用
    result[f'RSI{config.RSI_SHORT_PERIOD}'] = talib.RSI(close, timeperiod=config.RSI_SHORT_PERIOD)
    
    # 長期RSIを計算（例：14日）
    # 中長期的なトレンドの強さを測定するのに有用
    result[f'RSI{config.RSI_LONG_PERIOD}'] = talib.RSI(close, timeperiod=config.RSI_LONG_PERIOD)
    
    # 後方互換性のために長期RSIを「RSI」という標準名でも保存
    # 既存のシステムやコードとの互換性を維持するため
    result['RSI'] = result[f'RSI{config.RSI_LONG_PERIOD}']
    
    return result


def calculate_rci(df: pd.DataFrame) -> pd.DataFrame:
    """
    短期と長期のRCI（Rank Correlation Index）を計算します
    
    RCIは時間と価格の順位相関係数を利用したモメンタム指標です。
    RCIが+80以上で買われすぎ、-80以下で売られすぎを示し、
    トレンドの転換点を検出するのに役立ちます。
    
    Args:
        df: 株価データ（少なくともCloseカラムが必要）
        
    Returns:
        pd.DataFrame: RCIを追加したデータフレーム（短期RCI、長期RCI、買われすぎ/売られすぎ判定も追加）
    """
    import config
    
    # 元のデータを変更しないようにコピーを作成
    result = df.copy()
    # 終値の配列を取得
    close = df['Close'].values
    # データの長さを取得
    data_length = len(close)
    
    # 短期RCIの計算用の配列を初期化（NaNで埋める）
    rci_short = np.full(data_length, np.nan)
    short_period = config.RCI_SHORT_PERIOD  # 短期期間（例：9日）
    
    # 長期RCIの計算用の配列を初期化（NaNで埋める）
    rci_long = np.full(data_length, np.nan)
    long_period = config.RCI_LONG_PERIOD  # 長期期間（例：26日）
    
    # RCIの計算関数 - スピアマンの順位相関係数に基づく計算
    def compute_rci(period, i):
        # 十分なデータがない場合はNaNを返す
        if i < period - 1:
            return np.nan
            
        # 指定期間の価格データを取得
        price_window = close[i-period+1:i+1]
        
        # 時系列の順位を生成（最新が1、古いものが大きい値）
        time_ranks = np.arange(1, period + 1)
        
        # 価格の順位を計算（高い価格ほど順位が小さい値になる）
        # np.argsortがインデックスを返し、それを逆順にしてインデックス1から始める
        price_ranks = period - np.argsort(np.argsort(-price_window)) 
        
        # 時系列順位と価格順位の差の二乗和を計算
        d_squared = np.sum((time_ranks - price_ranks) ** 2)
        
        # RCI計算式：スピアマンの順位相関係数を百分率化
        # 1に近いほど時間と価格の相関が高い（上昇トレンド）
        # -1に近いほど時間と価格の相関が負（下降トレンド）
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
    
    # RCIの状態を判定（買われすぎ/売られすぎの基準値は±80）
    # RCI > 80：強い上昇トレンド（買われすぎの可能性）
    result['RCI_Short_Overbought'] = result[f'RCI{short_period}'] > 80
    # RCI < -80：強い下降トレンド（売られすぎの可能性）
    result['RCI_Short_Oversold'] = result[f'RCI{short_period}'] < -80
    result['RCI_Long_Overbought'] = result[f'RCI{long_period}'] > 80
    result['RCI_Long_Oversold'] = result[f'RCI{long_period}'] < -80
    
    return result


def calculate_ichimoku(df: pd.DataFrame) -> pd.DataFrame:
    """
    一目均衡表を計算します（shiftを使わない安全な実装）
    
    一目均衡表は日本で開発された複合的なテクニカル指標で、トレンドの方向性、
    強さ、支持/抵抗レベルを1つのチャート上に表示します。
    この実装では、pandas.shift()ではなく配列のインデックスを直接操作して
    より安全な計算を行います。
    
    Args:
        df: 株価データ（High, Low, Closeカラムが必要）
        
    Returns:
        pd.DataFrame: 一目均衡表のデータを追加したデータフレーム
                     （転換線、基準線、先行スパン、遅行スパン、各種判定結果を含む）
    """
    import config
    
    # 元のデータを変更しないようにコピーを作成
    result = df.copy()
    
    # 一目均衡表のパラメータを取得
    tenkan_period = config.ICHIMOKU_TENKAN_PERIOD       # 転換線期間（通常：9日）
    kijun_period = config.ICHIMOKU_KIJUN_PERIOD         # 基準線期間（通常：26日）
    senkou_span_b_period = config.ICHIMOKU_SENKOU_SPAN_B_PERIOD  # 先行スパンB期間（通常：52日）
    displacement = config.ICHIMOKU_DISPLACEMENT         # 先行表示期間（通常：26日）
    
    # 配列を直接操作するために、データをNumPy配列として取得
    high_values = df['High'].values    # 高値の配列
    low_values = df['Low'].values      # 安値の配列
    close_values = df['Close'].values  # 終値の配列
    
    # データの長さを取得
    data_length = len(high_values)
    
    # ===== 転換線（Tenkan-sen）の計算 =====
    # 計算式: (期間中の最高値 + 期間中の最安値) / 2
    # 短期的な価格のバランスポイントを示す
    tenkan_sen = np.full(data_length, np.nan)
    
    for i in range(tenkan_period - 1, data_length):
        period_high = np.max(high_values[i - tenkan_period + 1:i + 1])  # 期間内の最高値
        period_low = np.min(low_values[i - tenkan_period + 1:i + 1])    # 期間内の最安値
        tenkan_sen[i] = (period_high + period_low) / 2  # 中値を計算
    
    result['Ichimoku_Tenkan'] = tenkan_sen
    
    # ===== 基準線（Kijun-sen）の計算 =====
    # 計算式: (期間中の最高値 + 期間中の最安値) / 2
    # 中期的な価格のバランスポイントを示す
    kijun_sen = np.full(data_length, np.nan)
    
    for i in range(kijun_period - 1, data_length):
        period_high = np.max(high_values[i - kijun_period + 1:i + 1])  # 期間内の最高値
        period_low = np.min(low_values[i - kijun_period + 1:i + 1])    # 期間内の最安値
        kijun_sen[i] = (period_high + period_low) / 2  # 中値を計算
    
    result['Ichimoku_Kijun'] = kijun_sen
    
    # ===== 先行スパンA（Senkou Span A）の計算 =====
    # 計算式: (転換線 + 基準線) / 2
    # これを26日後（displacement日後）に表示する
    # 雲の上側の境界線を形成
    senkou_span_a = np.full(data_length, np.nan)
    
    for i in range(tenkan_period - 1, data_length):
        # 計算した値をdisplacement日後に表示（配列の範囲内のみ）
        if i + displacement < data_length:
            senkou_span_a[i + displacement] = (tenkan_sen[i] + kijun_sen[i]) / 2
    
    result['Ichimoku_SenkouA'] = senkou_span_a
    
    # ===== 先行スパンB（Senkou Span B）の計算 =====
    # 計算式: (期間中の最高値 + 期間中の最安値) / 2
    # これを26日後（displacement日後）に表示する
    # 雲の下側の境界線を形成
    senkou_span_b = np.full(data_length, np.nan)
    
    for i in range(senkou_span_b_period - 1, data_length):
        period_high = np.max(high_values[i - senkou_span_b_period + 1:i + 1])  # 期間内の最高値
        period_low = np.min(low_values[i - senkou_span_b_period + 1:i + 1])    # 期間内の最安値
        
        # 計算した値をdisplacement日後に表示（配列の範囲内のみ）
        if i + displacement < data_length:
            senkou_span_b[i + displacement] = (period_high + period_low) / 2
    
    result['Ichimoku_SenkouB'] = senkou_span_b
    
    # ===== 遅行スパン（Chikou Span）の計算 =====
    # 計算式: 現在の終値をdisplacement日前に表示
    # 価格と過去の関係を示す
    chikou_span = np.full(data_length, np.nan)
    
    for i in range(displacement, data_length):
        # 現在の終値をdisplacement日前の位置に配置
        chikou_span[i - displacement] = close_values[i]
    
    result['Ichimoku_Chikou'] = chikou_span
    
    # ===== 雲の判定 - 価格と雲の位置関係 =====
    # 価格が雲の上：強気市場、雲の下：弱気市場、雲の中：方向感なし
    result['Ichimoku_Above_Cloud'] = False  # 価格が雲の上にあるか
    result['Ichimoku_Below_Cloud'] = False  # 価格が雲の下にあるか
    result['Ichimoku_In_Cloud'] = False     # 価格が雲の中にあるか
    
    for i in range(data_length):
        # 先行スパンA, Bが両方とも計算されている場合のみ判定
        if not (np.isnan(senkou_span_a[i]) or np.isnan(senkou_span_b[i])):
            max_cloud = max(senkou_span_a[i], senkou_span_b[i])  # 雲の上端
            min_cloud = min(senkou_span_a[i], senkou_span_b[i])  # 雲の下端
            
            # 価格位置の判定と結果の設定
            if close_values[i] > max_cloud:
                result.loc[df.index[i], 'Ichimoku_Above_Cloud'] = True
            elif close_values[i] < min_cloud:
                result.loc[df.index[i], 'Ichimoku_Below_Cloud'] = True
            else:
                result.loc[df.index[i], 'Ichimoku_In_Cloud'] = True
    
    # ===== 雲の状態（文字列表現）=====
    # 日本語で雲との位置関係を表現（可視化・レポート用）
    result['Ichimoku_Cloud_Status'] = ''
    for i in range(data_length):
        if result.iloc[i]['Ichimoku_Above_Cloud']:
            result.iloc[i, result.columns.get_indexer(['Ichimoku_Cloud_Status'])[0]] = '雲の上'
        elif result.iloc[i]['Ichimoku_Below_Cloud']:
            result.iloc[i, result.columns.get_indexer(['Ichimoku_Cloud_Status'])[0]] = '雲の下'
        elif result.iloc[i]['Ichimoku_In_Cloud']:
            result.iloc[i, result.columns.get_indexer(['Ichimoku_Cloud_Status'])[0]] = '雲の中'
    
    # ===== 遅行線の判定 - 遅行線と価格の位置関係 =====
    # 遅行線が価格より上：上昇トレンドの可能性、下：下降トレンドの可能性
    result['Ichimoku_Chikou_Above_Price'] = False  # 遅行線が価格より上
    result['Ichimoku_Chikou_Below_Price'] = False  # 遅行線が価格より下
    
    for i in range(data_length - displacement):
        # 遅行線が計算されている場合のみ判定
        if not np.isnan(chikou_span[i]):
            price_at_chikou_time = close_values[i]  # 遅行線に対応する時点の価格
            
            # 遅行線と価格の位置関係を判定
            if chikou_span[i] > price_at_chikou_time:
                result.iloc[i + displacement, result.columns.get_indexer(['Ichimoku_Chikou_Above_Price'])[0]] = True
            elif chikou_span[i] < price_at_chikou_time:
                result.iloc[i + displacement, result.columns.get_indexer(['Ichimoku_Chikou_Below_Price'])[0]] = True
    
    # ===== 転換線と基準線の位置関係 =====
    # 転換線が基準線より上：短期的上昇傾向、下：短期的下降傾向
    result['Ichimoku_Tenkan_Above_Kijun'] = False  # 転換線が基準線より上
    result['Ichimoku_Tenkan_Below_Kijun'] = False  # 転換線が基準線より下
    
    for i in range(data_length):
        # 転換線と基準線が両方とも計算されている場合のみ判定
        if not (np.isnan(tenkan_sen[i]) or np.isnan(kijun_sen[i])):
            # 転換線と基準線の位置関係を判定
            if tenkan_sen[i] > kijun_sen[i]:
                result.iloc[i, result.columns.get_indexer(['Ichimoku_Tenkan_Above_Kijun'])[0]] = True
            elif tenkan_sen[i] < kijun_sen[i]:
                result.iloc[i, result.columns.get_indexer(['Ichimoku_Tenkan_Below_Kijun'])[0]] = True
    
    # ===== 三役好転・三役暗転の基本条件 =====
    # 三役好転：上昇トレンドへの転換シグナル
    # 三役暗転：下降トレンドへの転換シグナル
    result['SanYaku_Kouten'] = False  # 三役好転の基本条件
    result['SanYaku_Anten'] = False   # 三役暗転の基本条件
    
    for i in range(data_length):
        # 必要な値が全て存在する場合のみ判定
        if (i < data_length and 
            not pd.isna(result.iloc[i]['Ichimoku_Above_Cloud']) and 
            not pd.isna(result.iloc[i]['Ichimoku_Tenkan_Above_Kijun'])):
            
            # 遅行線の値が存在するか確認
            chikou_above_exists = not pd.isna(result.iloc[i].get('Ichimoku_Chikou_Above_Price', np.nan))
            chikou_below_exists = not pd.isna(result.iloc[i].get('Ichimoku_Chikou_Below_Price', np.nan))
            
            # 三役好転の基本条件：
            # 1. 価格が雲の上
            # 2. 遅行線が価格より上
            # 3. 転換線が基準線より上
            if chikou_above_exists:
                result.iloc[i, result.columns.get_indexer(['SanYaku_Kouten'])[0]] = (
                    result.iloc[i]['Ichimoku_Above_Cloud'] and 
                    result.iloc[i]['Ichimoku_Chikou_Above_Price'] and 
                    result.iloc[i]['Ichimoku_Tenkan_Above_Kijun']
                )
            
            # 三役暗転の基本条件：
            # 1. 価格が雲の下
            # 2. 遅行線が価格より下
            # 3. 転換線が基準線より下
            if chikou_below_exists:
                result.iloc[i, result.columns.get_indexer(['SanYaku_Anten'])[0]] = (
                    result.iloc[i]['Ichimoku_Below_Cloud'] and 
                    result.iloc[i]['Ichimoku_Chikou_Below_Price'] and 
                    result.iloc[i]['Ichimoku_Tenkan_Below_Kijun']
                )
    
    # ===== 三役好転・三役暗転の判定（転換線と基準線の交差を検出） =====
    # 三役好転・三役暗転は時系列的な変化も考慮して判定
    result['Ichimoku_SanYaku'] = ''  # 三役好転・三役暗転の結果
    
    # 前日と今日のデータを比較するため、最低2日分のデータが必要
    if data_length >= 2:
        for i in range(1, data_length):
            # 転換線または基準線が計算されていない場合はスキップ
            if (np.isnan(tenkan_sen[i-1]) or np.isnan(kijun_sen[i-1]) or 
                np.isnan(tenkan_sen[i]) or np.isnan(kijun_sen[i])):
                continue
            
            # 前日の値
            prev_tenkan = tenkan_sen[i-1]
            prev_kijun = kijun_sen[i-1]
            
            # 当日の値
            curr_tenkan = tenkan_sen[i]
            curr_kijun = kijun_sen[i]
            
            # 転換線が基準線を上抜けたか判定
            # 前日：転換線 <= 基準線、当日：転換線 > 基準線
            tenkan_uenuke = prev_tenkan <= prev_kijun and curr_tenkan > curr_kijun
            
            # 転換線が基準線を下抜けたか判定
            # 前日：転換線 >= 基準線、当日：転換線 < 基準線
            tenkan_shitanuke = prev_tenkan >= prev_kijun and curr_tenkan < curr_kijun
            
            # 三役好転の判定：
            # 1. 転換線が基準線を上抜けた
            # 2. 三役好転の基本条件を満たしている
            if tenkan_uenuke and result.iloc[i]['SanYaku_Kouten']:
                result.iloc[i, result.columns.get_indexer(['Ichimoku_SanYaku'])[0]] = '三役好転'
            
            # 三役暗転の判定：
            # 1. 転換線が基準線を下抜けた
            # 2. 三役暗転の基本条件を満たしている
            elif tenkan_shitanuke and result.iloc[i]['SanYaku_Anten']:
                result.iloc[i, result.columns.get_indexer(['Ichimoku_SanYaku'])[0]] = '三役暗転'
    
    return result


def calculate_trading_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    取引シグナル(Buy/Sell)を計算します
    
    すでに計算済みのテクニカル指標を組み合わせて、
    買いシグナルと売りシグナルを生成します。
    
    条件：
    Buy シグナル:
    - MACDがMACD_Signalを上回る（上昇モメンタム）
    - RSI短期がRSI長期を上回る（短期的な強さ）
    - RSI長期が40以下（まだ買われすぎではない）
    
    Sell シグナル:
    - MACDがMACD_Signalを下回る（下降モメンタム）
    - RSI短期がRSI長期を下回る（短期的な弱さ）
    - RSI長期が60以上（まだ売られすぎではない）
    
    Args:
        df: テクニカル指標が計算済みのデータフレーム
        
    Returns:
        pd.DataFrame: シグナル（Buy/Sell）を追加したデータフレーム
    """
    import config
    
    # 元のデータを変更しないようにコピーを作成
    result = df.copy()
    
    # 必要な列が存在するか確認
    # この関数はMACDとRSIの計算結果に依存するため、
    # これらのカラムが存在しない場合はエラーを出力
    required_columns = ['MACD', 'MACD_Signal', f'RSI{config.RSI_SHORT_PERIOD}', f'RSI{config.RSI_LONG_PERIOD}']
    missing_columns = [col for col in required_columns if col not in result.columns]
    
    if missing_columns:
        # 必要なカラムが不足している場合は警告ログを出力
        logger = logging.getLogger("StockSignal")
        logger.warning(f"シグナル計算に必要なカラムがありません: {missing_columns}")
        # 空のシグナル列を追加して処理を続行
        result['Signal'] = ''
        return result
    
    # シグナル列を追加（初期値は空文字列）
    result['Signal'] = ''
    
    # RSI短期・長期の列名を取得
    rsi_short_col = f'RSI{config.RSI_SHORT_PERIOD}'
    rsi_long_col = f'RSI{config.RSI_LONG_PERIOD}'
    
    # Buyシグナルの条件（以下の3条件をすべて満たす場合）
    # 1. MACD > MACD_Signal：上昇モメンタムが発生
    # 2. RSI短期 > RSI長期：短期的な上昇トレンドが発生
    # 3. RSI長期 <= 40：まだ買われすぎの状態ではない
    buy_condition = (
        (result['MACD'] > result['MACD_Signal']) & 
        (result[rsi_short_col] > result[rsi_long_col]) & 
        (result[rsi_long_col] <= 40)
    )
    
    # Sellシグナルの条件（以下の3条件をすべて満たす場合）
    # 1. MACD < MACD_Signal：下降モメンタムが発生
    # 2. RSI短期 < RSI長期：短期的な下降トレンドが発生
    # 3. RSI長期 >= 60：まだ売られすぎの状態ではない
    sell_condition = (
        (result['MACD'] < result['MACD_Signal']) & 
        (result[rsi_short_col] < result[rsi_long_col]) & 
        (result[rsi_long_col] >= 60)
    )
    
    # 条件に合致する行にシグナル値を設定
    result.loc[buy_condition, 'Signal'] = 'Buy'   # 買いシグナル
    result.loc[sell_condition, 'Signal'] = 'Sell'  # 売りシグナル