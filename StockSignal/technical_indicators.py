"""
テクニカル指標計算モジュール - 株価データから各種テクニカル指標を計算・シグナル生成

このモジュールは、株価データから様々なテクニカル指標を計算し、売買シグナルを生成します。
各テクニカル指標の計算関数と、それらを組み合わせて売買判断を行う機能を提供しています。
また、複数銘柄の一括処理や結果の保存機能も備えています。

計算対象テクニカル指標：
1. 移動平均線（SMA）- 短期(5日)、中期(25日)、長期(75日)
2. 出来高移動平均線（SMA）- 短期(5日)、中期(25日)、長期(75日)
3. MACD（Moving Average Convergence Divergence）
4. RSI（Relative Strength Index）- 短期(9日)、長期(14日)
5. RCI（Rank Correlation Index）- 短期(9日)、長期(26日)
6. 一目均衡表（Ichimoku Cloud）
7. ボリンジャーバンド（Bollinger Bands）
8. 移動平均線乖離率（MA Deviation）

シグナル生成：
- MACD-RSIシグナル
- MACD-RCIシグナル
- BB-MACDシグナル
- 移動平均線乖離率シグナル
- 一目均衡表シグナル

使用ライブラリ：
- TALib: テクニカル指標計算
- pandas: データ処理
- numpy: 数値計算

出力ファイル：
- latest_signal.csv: 全銘柄の最新テクニカル指標値
- 各銘柄の個別シグナルファイル（{ticker}_signal.csv）
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

def calculate_volume_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """
    出来高移動平均線を計算します
    
    config.MA_PERIODSで指定された期間の単純移動平均線（SMA）を計算します。
    出来高移動平均線は出来高のトレンドの方向性や強さを確認するための基本的な指標です。
    
    Args:
        df: 出来高データ（少なくともVolumeカラムが必要）
        
    Returns:
        pd.DataFrame: 出来高移動平均線を追加したデータフレーム（Volume_MA5, Volume_MA25, Volume_MA75）
    """
    import config
    
    result = df.copy()
    # 終値の配列を取得
    volume = df['Volume'].values
    
    # 設定された各期間の出来高移動平均線を計算
    for period in config.MA_PERIODS:
        result[f'Volume_MA{period}'] = talib.SMA(volume, timeperiod=period)
    return result

def calculate_trading_signals_MA_Deviation(df: pd.DataFrame) -> pd.DataFrame:
    """
    移動平均線乖離率に基づく取引シグナル(Buy/Sell)を計算します
    
    移動平均線からの乖離率を計算し、売られすぎ・買われすぎの状態を判定して
    売買シグナルを生成します。
    
    条件：
    Buy シグナル:
    - 短期移動平均線の乖離率が一定値以下（売られすぎ）
    - 短期移動平均線の前日比率がプラス（上昇に転じている）
    
    Sell シグナル:
    - 短期移動平均線の乖離率が一定値以上（買われすぎ）
    - 短期移動平均線の前日比率がマイナス（下落に転じている）
    
    Args:
        df: テクニカル指標が計算済みのデータフレーム
        
    Returns:
        pd.DataFrame: MA-Deviationシグナルを追加したデータフレーム
    """
    import config
    
    # 元のデータフレームを変更しないようにコピーを作成
    result = df.copy()
    
    # 短期移動平均線を選択（例：MA5など）
    short_period = min(config.MA_PERIODS)
    short_ma_column = f'MA{short_period}'
    short_ma_deviation_column = f'{short_ma_column}_Deviation'
    short_ma_change_column = f'{short_ma_column}_Change'
    
    # 必要な列が存在するか確認
    required_columns = [short_ma_deviation_column, short_ma_change_column]
    missing_columns = [col for col in required_columns if col not in result.columns]
    
    # 必要なカラムが一つでも欠けている場合は処理を中断
    if missing_columns:
        logger = logging.getLogger("StockSignal")
        logger.warning(f"MA-Deviationシグナル計算に必要なカラムがありません: {missing_columns}")
        result['MA-Deviation'] = ''
        return result
    
    # シグナル列を初期化
    result['MA-Deviation'] = ''
    
    # 乖離率の閾値（例: -3%以下で買い、3%以上で売り）※パラメータは要検討
    buy_threshold = -3.0
    sell_threshold = 3.0
    
    # Buyシグナルの条件（押し目の判定）
    buy_condition = (
        (result[short_ma_deviation_column] <= buy_threshold) & 
        (result[short_ma_change_column] > 0)
    )
    
    # Sellシグナルの条件（押し目の判定）
    sell_condition = (
        (result[short_ma_deviation_column] >= sell_threshold) & 
        (result[short_ma_change_column] < 0)
    )
    
    # 条件に合致する行にシグナル値を設定　※これをどう使用するかは要検討
    result.loc[buy_condition, 'MA-Deviation'] = 'Buy'
    result.loc[sell_condition, 'MA-Deviation'] = 'Sell'
    
    return result


def calculate_ma_deviation_and_change(df: pd.DataFrame) -> pd.DataFrame:
    """
    移動平均線乖離率と移動平均線の前日比率を計算します
    
    乖離率は「(現在値-移動平均線)/移動平均線×100」で計算され、
    前日比率は「今日の移動平均線/前日の移動平均線×100-100」で計算されます。
    
    Args:
        df: 株価データと移動平均線が計算済みのデータフレーム
        
    Returns:
        pd.DataFrame: 乖離率と前日比率を追加したデータフレーム
    """
    import config
    
    # 元のデータを変更しないようにコピーを作成
    result = df.copy()
    
    # 終値の配列を取得
    close = df['Close'].values
    
    # 設定された各期間の移動平均線について乖離率と前日比率を計算
    for period in config.MA_PERIODS:
        ma_column = f'MA{period}'
        
        # 移動平均線が計算されていない場合はスキップ
        if ma_column not in result.columns:
            continue
        
        # 乖離率の計算: (現在値-移動平均線)/移動平均線×100
        result[f'{ma_column}_Deviation'] = ((close - result[ma_column]) / result[ma_column]) * 100
        
        # 前日比率の計算: 今日の移動平均線/前日の移動平均線×100-100
        # shift(1)で前日の値を取得し、その差からパーセント変化を計算
        result[f'{ma_column}_Change'] = (result[ma_column] / result[ma_column].shift(1) * 100) - 100
    
    return result

def calculate_bollinger_bands(df: pd.DataFrame) -> pd.DataFrame:
    """
    ボリンジャーバンドを計算します
    
    ボリンジャーバンドは価格の変動幅を統計的に表示するテクニカル指標です。
    - ミドルバンド：指定期間の単純移動平均線（通常20日）
    - アッパーバンド：ミドルバンド + （標準偏差 × 倍率）
    - ローワーバンド：ミドルバンド - （標準偏差 × 倍率）
    
    価格がバンドの外側に出ることは統計的に稀であり、
    トレンドの転換点や売買のタイミングを判断する指標として使用されます。
    
    Args:
        df: 株価データ（少なくともCloseカラムが必要）
        
    Returns:
        pd.DataFrame: ボリンジャーバンドを追加したデータフレーム
    """
    import config
    
    # 元のデータを変更しないようにコピーを作成
    result = df.copy()
    # 終値の配列を取得
    close = df['Close'].values
    
    # TALibを使用してボリンジャーバンドを計算
    # 戻り値: アッパーバンド、ミドルバンド、ローワーバンド
    upper_band, middle_band, lower_band = talib.BBANDS(
        close,
        timeperiod=config.BOLLINGER_PERIOD,      # 期間（通常：20日）
        nbdevup=config.BOLLINGER_STD_DEV,        # 上側の標準偏差倍率（通常：2）
        nbdevdn=config.BOLLINGER_STD_DEV,        # 下側の標準偏差倍率（通常：2）
        matype=0                                 # 移動平均の種類（0=SMA）
    )
    
    # 計算結果をデータフレームに追加
    result['BB_Upper'] = upper_band       # アッパーバンド
    result['BB_Middle'] = middle_band     # ミドルバンド（20SMA）
    result['BB_Lower'] = lower_band       # ローワーバンド
    
    # ボリンジャーバンドの幅を計算（アッパーバンド - ローワーバンド）
    # バンドの幅はボラティリティの指標として使用される
    result['BB_Width'] = upper_band - lower_band
    
    # ボリンジャーバンド%B を計算
    # %B = (価格 - ローワーバンド) / (アッパーバンド - ローワーバンド)
    # 0.5でミドルバンド、1.0でアッパーバンド、0.0でローワーバンドを示す
    band_range = upper_band - lower_band
    # ゼロ除算を防ぐため、バンド幅が0でない場合のみ計算
    result['BB_PercentB'] = np.where(
        band_range != 0,
        (close - lower_band) / band_range,
        np.nan
    )
    
    # 価格とバンドの位置関係を判定
    result['BB_Above_Upper'] = close > upper_band    # 価格がアッパーバンドより上
    result['BB_Below_Lower'] = close < lower_band    # 価格がローワーバンドより下
    result['BB_In_Band'] = (close >= lower_band) & (close <= upper_band)  # 価格がバンド内
    
    # ボリンジャーバンドスクイーズの検出
    # スクイーズ：バンド幅が過去の平均より狭くなった状態（ボラティリティの低下）
    # 過去20日のバンド幅の移動平均と比較
    bb_width_ma = talib.SMA(result['BB_Width'].values, timeperiod=20)
    result['BB_Squeeze'] = result['BB_Width'] < bb_width_ma * 0.8  # 80%以下でスクイーズと判定
    
    return result


def calculate_trading_signals_bollinger(df: pd.DataFrame) -> pd.DataFrame:
    """
    ボリンジャーバンドに基づく取引シグナル(Buy/Sell)を計算します
    
    条件：
    Buy シグナル:
    - 価格がローワーバンドを下回った後、ローワーバンドを上回る
    - %Bが0.2以下から0.2を上回る（売られすぎからの回復）
    
    Sell シグナル:
    - 価格がアッパーバンドを上回った後、アッパーバンドを下回る
    - %Bが0.8以上から0.8を下回る（買われすぎからの調整）
    
    Args:
        df: ボリンジャーバンドが計算済みのデータフレーム
        
    Returns:
        pd.DataFrame: ボリンジャーバンドシグナルを追加したデータフレーム
    """
    # 元のデータフレームを変更しないようにコピーを作成
    result = df.copy()
    
    # 必要な列が存在するか確認
    required_columns = ['BB_Upper', 'BB_Lower', 'BB_PercentB', 'Close']
    missing_columns = [col for col in required_columns if col not in result.columns]
    
    # 必要なカラムが一つでも欠けている場合は処理を中断
    if missing_columns:
        logger = logging.getLogger("StockSignal")
        logger.warning(f"ボリンジャーバンドシグナル計算に必要なカラムがありません: {missing_columns}")
        result['BB-Signal'] = ''
        return result
    
    # シグナル列を初期化
    result['BB-Signal'] = ''
    
    # データが2行以上ある場合のみシグナル計算を実行
    if len(result) >= 2:
        for i in range(1, len(result)):
            # 前日と当日のデータを取得
            prev_close = result.iloc[i-1]['Close']
            curr_close = result.iloc[i]['Close']
            prev_percent_b = result.iloc[i-1]['BB_PercentB']
            curr_percent_b = result.iloc[i]['BB_PercentB']
            upper_band = result.iloc[i]['BB_Upper']
            lower_band = result.iloc[i]['BB_Lower']
            
            # NaN値のチェック
            if pd.isna(prev_percent_b) or pd.isna(curr_percent_b):
                continue
            
            # Buyシグナルの条件
            # 1. %Bが0.2以下から0.2を上回る（売られすぎからの回復）
            # 2. 価格がローワーバンドを下回った後、上回る
            buy_condition_1 = prev_percent_b <= 0.2 and curr_percent_b > 0.2
            buy_condition_2 = prev_close < lower_band and curr_close >= lower_band
            
            # Sellシグナルの条件
            # 1. %Bが0.8以上から0.8を下回る（買われすぎからの調整）
            # 2. 価格がアッパーバンドを上回った後、下回る
            sell_condition_1 = prev_percent_b >= 0.8 and curr_percent_b < 0.8
            sell_condition_2 = prev_close > upper_band and curr_close <= upper_band
            
            # シグナルの設定
            if buy_condition_1 or buy_condition_2:
                result.iloc[i, result.columns.get_indexer(['BB-Signal'])[0]] = 'Buy'
            elif sell_condition_1 or sell_condition_2:
                result.iloc[i, result.columns.get_indexer(['BB-Signal'])[0]] = 'Sell'
    
    return result


def calculate_bollinger_band_position(df: pd.DataFrame) -> pd.DataFrame:
    """
    ボリンジャーバンドにおける価格の位置関係をより詳細に分析します
    
    Args:
        df: ボリンジャーバンドが計算済みのデータフレーム
        
    Returns:
        pd.DataFrame: 詳細な位置関係分析を追加したデータフレーム
    """
    result = df.copy()
    
    # 必要な列が存在するか確認
    required_columns = ['BB_Upper', 'BB_Middle', 'BB_Lower', 'Close']
    missing_columns = [col for col in required_columns if col not in result.columns]
    
    if missing_columns:
        logger = logging.getLogger("StockSignal")
        logger.warning(f"ボリンジャーバンド位置分析に必要なカラムがありません: {missing_columns}")
        return result
    
    # 価格のバンド内位置を文字列で表現
    result['BB_Position'] = ''
    
    for i in range(len(result)):
        close = result.iloc[i]['Close']
        upper = result.iloc[i]['BB_Upper']
        middle = result.iloc[i]['BB_Middle']
        lower = result.iloc[i]['BB_Lower']
        
        # NaN値チェック
        if pd.isna(close) or pd.isna(upper) or pd.isna(middle) or pd.isna(lower):
            result.iloc[i, result.columns.get_indexer(['BB_Position'])[0]] = 'データ不足'
            continue
        
        # 価格位置の判定
        if close > upper:
            result.iloc[i, result.columns.get_indexer(['BB_Position'])[0]] = 'アッパーバンド超え'
        elif close > middle:
            result.iloc[i, result.columns.get_indexer(['BB_Position'])[0]] = 'ミドル〜アッパー'
        elif close > lower:
            result.iloc[i, result.columns.get_indexer(['BB_Position'])[0]] = 'ロワー〜ミドル'
        else:
            result.iloc[i, result.columns.get_indexer(['BB_Position'])[0]] = 'ローワーバンド下'
    
    # ミドルバンド（20SMA）との乖離率を計算
    result['BB_Middle_Deviation'] = ((result['Close'] - result['BB_Middle']) / result['BB_Middle']) * 100
    
    # バンド幅の前日比変化率を計算
    result['BB_Width_Change'] = result['BB_Width'].pct_change() * 100
    
    # ボリンジャーバンドウォーク（連続してバンド外にある状態）の検出
    result['BB_Walk_Up'] = False    # 連続してアッパーバンド外
    result['BB_Walk_Down'] = False  # 連続してローワーバンド外
    
    # 連続判定のための処理
    consecutive_up = 0
    consecutive_down = 0
    
    for i in range(len(result)):
        if result.iloc[i]['BB_Above_Upper']:
            consecutive_up += 1
            consecutive_down = 0
        elif result.iloc[i]['BB_Below_Lower']:
            consecutive_down += 1
            consecutive_up = 0
        else:
            consecutive_up = 0
            consecutive_down = 0
        
        # 2日以上連続でバンド外にある場合をウォークとして判定
        if consecutive_up >= 2:
            result.iloc[i, result.columns.get_indexer(['BB_Walk_Up'])[0]] = True
        if consecutive_down >= 2:
            result.iloc[i, result.columns.get_indexer(['BB_Walk_Down'])[0]] = True
    
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
    
    Args:
        df: 株価データ
        
    Returns:
        pd.DataFrame: 一目均衡表のデータを追加したデータフレーム
    """
    import config
    
    # 元のデータを変更しないようにコピーを作成
    result = df.copy()
    
    # パラメータの取得
    tenkan_period = config.ICHIMOKU_TENKAN_PERIOD                # 転換線期間
    kijun_period = config.ICHIMOKU_KIJUN_PERIOD                  # 基準線期間
    senkou_span_b_period = config.ICHIMOKU_SENKOU_SPAN_B_PERIOD  # 先行スパンB期間
    displacement = config.ICHIMOKU_DISPLACEMENT                  # 先行表示期間
    
    # 配列を直接操作するために、データをNumPy配列として取得
    high_values = df['High'].values
    low_values = df['Low'].values
    close_values = df['Close'].values
    
    # データ長
    data_length = len(high_values)
    
    # ===== 転換線（Tenkan-sen）の計算 =====
    # 計算式: (期間中の最高値 + 期間中の最安値) / 2
    # 短期的な価格のバランスポイントを示す
    tenkan_sen = np.full(data_length, np.nan)
    
    for i in range(tenkan_period - 1, data_length):
        period_high = np.max(high_values[i - tenkan_period + 1:i + 1])  # 期間内の最高値
        period_low = np.min(low_values[i - tenkan_period + 1:i + 1])    # 期間内の最安値
        tenkan_sen[i] = (period_high + period_low) / 2                  # 中値を計算
    
    result['Ichimoku_Tenkan'] = tenkan_sen
    
    # ===== 基準線（Kijun-sen）の計算 =====
    # 計算式: (期間中の最高値 + 期間中の最安値) / 2
    # 中期的な価格のバランスポイントを示す
    kijun_sen = np.full(data_length, np.nan)
    
    for i in range(kijun_period - 1, data_length):
        period_high = np.max(high_values[i - kijun_period + 1:i + 1])  # 期間内の最高値
        period_low = np.min(low_values[i - kijun_period + 1:i + 1])    # 期間内の最安値
        kijun_sen[i] = (period_high + period_low) / 2                  # 中値を計算
    
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
        # インデックス外アクセスの防止とすべての必要な値が存在することを確認
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
    
    # 判定日付用の列を追加し初期化
    result['Ichimoku_JudgeDate'] = ''
    
    # 三役好転・三役暗転の判定（トレンド転換）
    result['Ichimoku_SanYaku'] = ''  # 三役好転・三役暗転の結果
    
    # 前日と今日のデータを使用して判定するため、2行以上のデータが必要
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
            
            # 転換線が基準線を上抜けたか判定（前日は基準線以下、当日は基準線より上）
            tenkan_uenuke = prev_tenkan <= prev_kijun and curr_tenkan > curr_kijun
            
            # 転換線が基準線を下抜けたか判定（前日は基準線以上、当日は基準線より下）
            tenkan_shitanuke = prev_tenkan >= prev_kijun and curr_tenkan < curr_kijun
            
            # 日付フォーマット (YYYY-MM-DD) 取得
            try:
                date_str = df.index[i].strftime('%Y-%m-%d')
            except:
                date_str = ""  # インデックスが日付でない場合は空文字
            
            # 三役好転: 基本条件を満たしている場合
            if result.iloc[i]['SanYaku_Kouten']:
                result.iloc[i, result.columns.get_indexer(['Ichimoku_SanYaku'])[0]] = '三役好転'
                
                # 転換があった場合は日付を記録
                if tenkan_uenuke:
                    result.iloc[i, result.columns.get_indexer(['Ichimoku_JudgeDate'])[0]] = date_str
            
            # 三役暗転: 基本条件を満たしている場合
            elif result.iloc[i]['SanYaku_Anten']:
                result.iloc[i, result.columns.get_indexer(['Ichimoku_SanYaku'])[0]] = '三役暗転'
                
                # 転換があった場合は日付を記録
                if tenkan_shitanuke:
                    result.iloc[i, result.columns.get_indexer(['Ichimoku_JudgeDate'])[0]] = date_str
    
    return result


def calculate_trading_signals_MACD_RSI(df: pd.DataFrame) -> pd.DataFrame:
    """
    MACDとRSIによる取引シグナル(Buy/Sell)を計算します
    
    条件：
    Buy シグナル:
    - MACDがMACD_Signalを上回る
    - RSI短期がRSI長期を上回る
    - RSI長期が40以下
    
    Sell シグナル:
    - MACDがMACD_Signalを下回る
    - RSI短期がRSI長期を下回る
    - RSI長期が60以上
    
    Args:
        df: テクニカル指標が計算済みのデータフレーム
        
    Returns:
        pd.DataFrame: MACD-RSIシグナルを追加したデータフレーム
    """
    import config  # 設定値を取得するために設定モジュールをインポート
    
    # 元のデータフレームを変更しないようにコピーを作成
    result = df.copy()
    
    # 必要な列が存在するか確認
    # シグナル計算には特定のテクニカル指標が必要なため、それらのカラムの存在を検証
    required_columns = ['MACD', 'MACD_Signal', f'RSI{config.RSI_SHORT_PERIOD}', f'RSI{config.RSI_LONG_PERIOD}']
    # リスト内包表記を使用して、存在しないカラムをリストアップ
    missing_columns = [col for col in required_columns if col not in result.columns]
    
    # 必要なカラムが一つでも欠けている場合は処理を中断
    if missing_columns:
        # ロガーを取得してエラーメッセージを記録
        logger = logging.getLogger("StockSignal")
        logger.warning(f"シグナル計算に必要なカラムがありません: {missing_columns}")
        # シグナル列を空文字で追加して返す（エラー回避のため）
        result['MACD-RSI'] = ''
        return result
    
    # 必要な列がすべて存在する場合は、シグナル列を初期化（空文字列）
    result['MACD-RSI'] = ''
    
    # RSI短期・長期の列名を取得（設定に応じた期間の列名を動的に生成）
    rsi_short_col = f'RSI{config.RSI_SHORT_PERIOD}'  # 例: RSI9
    rsi_long_col = f'RSI{config.RSI_LONG_PERIOD}'    # 例: RSI14
    
    # Buyシグナルの条件を定義（3条件の論理積）
    # 1. MACDがシグナル線を上回る（上昇モメンタムの発生）
    # 2. 短期RSIが長期RSIを上回る（短期的な強さの表れ）
    # 3. 長期RSIが40以下（まだ買われすぎではなく、上昇余地がある）
    buy_condition = (
        (result['MACD'] > result['MACD_Signal']) & 
        (result[rsi_short_col] > result[rsi_long_col]) & 
        (result[rsi_long_col] <= 40)
    )
    
    # Sellシグナルの条件を定義（3条件の論理積）
    # 1. MACDがシグナル線を下回る（下降モメンタムの発生）
    # 2. 短期RSIが長期RSIを下回る（短期的な弱さの表れ）
    # 3. 長期RSIが60以上（まだ売られすぎではなく、下落余地がある）
    sell_condition = (
        (result['MACD'] < result['MACD_Signal']) & 
        (result[rsi_short_col] < result[rsi_long_col]) & 
        (result[rsi_long_col] >= 60)
    )
    
    # 条件に合致する行にシグナル値を設定
    # pandas.DataFrameのloc[]を使用して、条件を満たす行のみを更新
    result.loc[buy_condition, 'MACD-RSI'] = 'Buy'    # 買いシグナル設定
    result.loc[sell_condition, 'MACD-RSI'] = 'Sell'  # 売りシグナル設定
    
    return result


def calculate_trading_signals_MACD_RCI(df: pd.DataFrame) -> pd.DataFrame:
    """
    取引シグナル(Buy/Sell)を計算します（MACDとRCIを使用）
    
    条件：
    Buy シグナル:
    - 直近5営業日内にRCIが-80を上回る
    - MACDがMACD_Signalを上回る
    - RCI短期が50以上
    
    Sell シグナル:
    - 直近5営業日内にRCIが80を下回る
    - MACDがMACD_Signalを下回る
    - RCI短期が-50以下
    
    Args:
        df: テクニカル指標が計算済みのデータフレーム
        
    Returns:
        pd.DataFrame: MACD-RCIシグナルを追加したデータフレーム
    """
    import config  # 設定値を取得するために設定モジュールをインポート
    
    # 元のデータフレームを変更しないようにコピーを作成
    result = df.copy()
    
    # 必要な列が存在するか確認
    # シグナル計算には特定のテクニカル指標が必要なため、それらのカラムの存在を検証
    rci_long_column = f'RCI{config.RCI_LONG_PERIOD}'  # RCI長期を使用
    rci_short_column = f'RCI{config.RCI_SHORT_PERIOD}'  # RCI短期を使用
    required_columns = ['MACD', 'MACD_Signal', rci_long_column, rci_short_column]
    # リスト内包表記を使用して、存在しないカラムをリストアップ
    missing_columns = [col for col in required_columns if col not in result.columns]
    
    # 必要なカラムが一つでも欠けている場合は処理を中断
    if missing_columns:
        # ロガーを取得してエラーメッセージを記録
        logger = logging.getLogger("StockSignal")
        logger.warning(f"MACD-RCIシグナル計算に必要なカラムがありません: {missing_columns}")
        # シグナル列を空文字で追加して返す（エラー回避のため）
        result['MACD-RCI'] = ''
        return result
    
    # 必要な列がすべて存在する場合は、シグナル列を初期化（空文字列）
    result['MACD-RCI'] = ''
    
    # データが5行以上あるか確認（直近5営業日の判定に必要）
    if len(result) < 5:
        logger = logging.getLogger("StockSignal")
        logger.warning(f"MACD-RCIシグナル計算には少なくとも5日分のデータが必要です")
        return result
    
    # 各行に対して直近5営業日のRCIのチェックを行う
    for i in range(4, len(result)):
        # 現在の日付と直近5営業日のデータを取得
        current_idx = result.index[i]
        past_5days = result.iloc[i-4:i+1]  # 現在の日付を含む5営業日分のデータ
        
        # MACDシグナルとの関係を確認
        macd_above_signal = result.iloc[i]['MACD'] > result.iloc[i]['MACD_Signal']
        macd_below_signal = result.iloc[i]['MACD'] < result.iloc[i]['MACD_Signal']
        
        # RCI短期の条件を確認
        rci_short_above_50 = result.iloc[i][rci_short_column] >= 50
        rci_short_below_minus_50 = result.iloc[i][rci_short_column] <= -50
        
        # 直近5営業日内でRCIが-80を上回ったかチェック（Buyシグナル用）
        rci_crosses_above_minus_80 = False
        for j in range(len(past_5days) - 1):
            if past_5days.iloc[j][rci_long_column] <= -80 and past_5days.iloc[j+1][rci_long_column] > -80:
                rci_crosses_above_minus_80 = True
                break
        
        # 直近5営業日内でRCIが80を下回ったかチェック（Sellシグナル用）
        rci_crosses_below_80 = False
        for j in range(len(past_5days) - 1):
            if past_5days.iloc[j][rci_long_column] >= 80 and past_5days.iloc[j+1][rci_long_column] < 80:
                rci_crosses_below_80 = True
                break
        
        # Buyシグナルの条件を確認（追加条件：RCI短期が50以上）
        if rci_crosses_above_minus_80 and macd_above_signal and rci_short_above_50:
            result.loc[current_idx, 'MACD-RCI'] = 'Buy'
        
        # Sellシグナルの条件を確認（追加条件：RCI短期が-50以下）
        elif rci_crosses_below_80 and macd_below_signal and rci_short_below_minus_50:
            result.loc[current_idx, 'MACD-RCI'] = 'Sell'
    
    return result

def calculate_trading_signals_BB_MACD(df: pd.DataFrame) -> pd.DataFrame:
    """
    ボリンジャーバンド（20SMA）とMACDを組み合わせた取引シグナル(Buy/Sell)を計算します
    
    買いシグナル条件：
    - 終値が20SMA（BB_Middle）を上回る
    - 最新のMACDはMACDシグナルを上回っている
    - 2営業日前のMACDはMACDシグナルを下回っている
    
    売りシグナル条件：
    - 終値が20SMA（BB_Middle）を下回る
    - 最新のMACDはMACDシグナルを下回っている
    - 2営業日前のMACDはMACDシグナルを上回っている
    
    Args:
        df: ボリンジャーバンドとMACDが計算済みのデータフレーム
        
    Returns:
        pd.DataFrame: BB-MACDシグナルを追加したデータフレーム
    """
    # ロガーを取得
    logger = logging.getLogger("StockSignal")
    
    # 元のデータフレームを変更しないようにコピーを作成
    result = df.copy()
    
    # 必要な列が存在するか確認
    required_columns = ['Close', 'BB_Middle', 'MACD', 'MACD_Signal']
    missing_columns = [col for col in required_columns if col not in result.columns]
    
    # 必要なカラムが一つでも欠けている場合は処理を中断
    if missing_columns:
        logger.warning(f"BB-MACDシグナル計算に必要なカラムがありません: {missing_columns}")
        result['BB-MACD'] = ''
        return result
    
    # シグナル列を初期化
    result['BB-MACD'] = ''
    
    # データが3行以上ある場合のみシグナル計算を実行（2営業日前のデータが必要なため）
    if len(result) < 3:
        logger.warning("BB-MACDシグナル計算には少なくとも3日分のデータが必要です")
        return result
    
    # 各行に対してシグナル判定を実行（i=2から開始：2営業日前のデータが必要）
    for i in range(2, len(result)):
        # 当日のデータを取得
        curr_close = result.iloc[i]['Close']
        curr_bb_middle = result.iloc[i]['BB_Middle']
        curr_macd = result.iloc[i]['MACD']
        curr_macd_signal = result.iloc[i]['MACD_Signal']
        
        # 2営業日前のデータを取得
        macd_2days_ago = result.iloc[i-2]['MACD']
        macd_signal_2days_ago = result.iloc[i-2]['MACD_Signal']
        
        # NaN値のチェック
        if (pd.isna(curr_close) or pd.isna(curr_bb_middle) or 
            pd.isna(curr_macd) or pd.isna(curr_macd_signal) or
            pd.isna(macd_2days_ago) or pd.isna(macd_signal_2days_ago)):
            continue
        
        # ボリンジャーバンド条件の判定
        price_above_20sma = curr_close > curr_bb_middle  # 終値が20SMAを上回る
        price_below_20sma = curr_close < curr_bb_middle  # 終値が20SMAを下回る
        
        # MACD条件の判定（クロスオーバーの検出）
        macd_bullish_today = curr_macd > curr_macd_signal                # 当日MACDがシグナル上回る
        macd_bearish_2days_ago = macd_2days_ago < macd_signal_2days_ago  # 2営業日前MACDがシグナル下回る
        macd_bearish_today = curr_macd < curr_macd_signal                # 当日MACDがシグナル下回る
        macd_bullish_2days_ago = macd_2days_ago > macd_signal_2days_ago  # 2営業日前MACDがシグナル上回る
        
        # MACDクロスオーバー条件
        macd_bullish_crossover = macd_bullish_today and macd_bearish_2days_ago  # ゴールデンクロス
        macd_bearish_crossover = macd_bearish_today and macd_bullish_2days_ago  # デッドクロス
        
        # 買いシグナルの総合判定
        buy_condition = price_above_20sma and macd_bullish_crossover
        
        # 売りシグナルの総合判定
        sell_condition = price_below_20sma and macd_bearish_crossover
        
        # シグナルの設定
        if buy_condition:
            result.iloc[i, result.columns.get_indexer(['BB-MACD'])[0]] = 'Buy'
        elif sell_condition:
            result.iloc[i, result.columns.get_indexer(['BB-MACD'])[0]] = 'Sell'
    
    return result


def calculate_trading_signals_BB_MACD_detailed(df: pd.DataFrame) -> pd.DataFrame:
    """
    ボリンジャーバンド（20SMA）とMACDを組み合わせた詳細な取引シグナルを計算します
    
    この関数は上記の基本シグナルに加えて、詳細な判定理由も記録します。
    
    Args:
        df: ボリンジャーバンドとMACDが計算済みのデータフレーム
        
    Returns:
        pd.DataFrame: 詳細なBB-MACDシグナル情報を追加したデータフレーム
    """
    # ロガーを取得
    logger = logging.getLogger("StockSignal")
    
    # 元のデータフレームを変更しないようにコピーを作成
    result = df.copy()
    
    # 必要な列が存在するか確認
    required_columns = ['Close', 'BB_Middle', 'MACD', 'MACD_Signal']
    missing_columns = [col for col in required_columns if col not in result.columns]
    
    if missing_columns:
        logger.warning(f"BB-MACD詳細シグナル計算に必要なカラムがありません: {missing_columns}")
        # 詳細情報用の列を初期化
        result['BB-MACD_Detail'] = ''
        result['BB_Condition'] = False
        result['MACD_Condition'] = False
        result['MACD_Signal_Day'] = ''
        return result
    
    # 詳細情報用の列を初期化
    result['BB-MACD_Detail'] = ''
    result['BB_Condition'] = False       # ボリンジャーバンド条件満たすか
    result['MACD_Condition'] = False     # MACD条件満たすか
    result['MACD_Signal_Day'] = ''       # MACDシグナルが発生した日（当日/前日）
    result['Price_20SMA_Diff'] = 0.0     # 価格と20SMAの差額
    result['Price_20SMA_Diff_Pct'] = 0.0 # 価格と20SMAの差の割合
    
    # データが2行以上ある場合のみ計算実行
    if len(result) < 2:
        logger.warning("BB-MACD詳細シグナル計算には少なくとも2日分のデータが必要です")
        return result
    
    # 各行に対して詳細分析を実行
    for i in range(1, len(result)):
        # 当日のデータを取得
        curr_close = result.iloc[i]['Close']
        curr_bb_middle = result.iloc[i]['BB_Middle']
        curr_macd = result.iloc[i]['MACD']
        curr_macd_signal = result.iloc[i]['MACD_Signal']
        
        # 前日のデータを取得
        prev_macd = result.iloc[i-1]['MACD']
        prev_macd_signal = result.iloc[i-1]['MACD_Signal']
        
        # NaN値のチェック
        if (pd.isna(curr_close) or pd.isna(curr_bb_middle) or 
            pd.isna(curr_macd) or pd.isna(curr_macd_signal) or
            pd.isna(prev_macd) or pd.isna(prev_macd_signal)):
            continue
        
        # 価格と20SMAの差を計算
        price_diff = curr_close - curr_bb_middle
        price_diff_pct = (price_diff / curr_bb_middle) * 100
        
        result.iloc[i, result.columns.get_indexer(['Price_20SMA_Diff'])[0]] = price_diff
        result.iloc[i, result.columns.get_indexer(['Price_20SMA_Diff_Pct'])[0]] = price_diff_pct
        
        # ボリンジャーバンド条件の判定
        bb_buy_condition = curr_close > curr_bb_middle
        bb_sell_condition = curr_close < curr_bb_middle
        
        # MACD条件の判定
        macd_bullish_today = curr_macd > curr_macd_signal
        macd_bullish_yesterday = prev_macd > prev_macd_signal
        macd_bearish_today = curr_macd < curr_macd_signal
        macd_bearish_yesterday = prev_macd < prev_macd_signal
        
        # MACDシグナル発生日の特定
        macd_signal_day = ''
        macd_bullish_condition = False
        macd_bearish_condition = False
        
        if macd_bullish_today and macd_bullish_yesterday:
            macd_signal_day = '当日・前日両方'
            macd_bullish_condition = True
        elif macd_bullish_today:
            macd_signal_day = '当日'
            macd_bullish_condition = True
        elif macd_bullish_yesterday:
            macd_signal_day = '前日'
            macd_bullish_condition = True
        elif macd_bearish_today and macd_bearish_yesterday:
            macd_signal_day = '当日・前日両方'
            macd_bearish_condition = True
        elif macd_bearish_today:
            macd_signal_day = '当日'
            macd_bearish_condition = True
        elif macd_bearish_yesterday:
            macd_signal_day = '前日'
            macd_bearish_condition = True
        
        # 条件満了の記録
        if bb_buy_condition:
            result.iloc[i, result.columns.get_indexer(['BB_Condition'])[0]] = True
        elif bb_sell_condition:
            result.iloc[i, result.columns.get_indexer(['BB_Condition'])[0]] = True
        
        if macd_bullish_condition or macd_bearish_condition:
            result.iloc[i, result.columns.get_indexer(['MACD_Condition'])[0]] = True
            result.iloc[i, result.columns.get_indexer(['MACD_Signal_Day'])[0]] = macd_signal_day
        
        # 総合的な詳細シグナル判定
        detail_text = ''
        
        if bb_buy_condition and macd_bullish_condition:
            detail_text = f'Buy: 価格20SMA上回り({price_diff_pct:.2f}%) + MACD強気({macd_signal_day})'
        elif bb_sell_condition and macd_bearish_condition:
            detail_text = f'Sell: 価格20SMA下回り({price_diff_pct:.2f}%) + MACD弱気({macd_signal_day})'
        elif bb_buy_condition:
            detail_text = f'BB条件のみ: 価格20SMA上回り({price_diff_pct:.2f}%) - MACD条件不足'
        elif bb_sell_condition:
            detail_text = f'BB条件のみ: 価格20SMA下回り({price_diff_pct:.2f}%) - MACD条件不足'
        elif macd_bullish_condition:
            detail_text = f'MACD条件のみ: MACD強気({macd_signal_day}) - 価格20SMA下回り'
        elif macd_bearish_condition:
            detail_text = f'MACD条件のみ: MACD弱気({macd_signal_day}) - 価格20SMA上回り'
        
        result.iloc[i, result.columns.get_indexer(['BB-MACD_Detail'])[0]] = detail_text
    
    return result

def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    すべてのテクニカル指標を計算します
    
    Args:
        df: 株価データ
        
    Returns:
        pd.DataFrame: テクニカル指標を追加したデータフレーム
    """
    # 元のデータフレームを変更しないようにコピーを作成
    result = df.copy()
    
    # 移動平均線の計算
    result = calculate_moving_averages(result)
    
    # 出来高移動平均線の計算
    result = calculate_volume_moving_averages(result)
    
    # 移動平均線乖離率と前日比率の計算
    result = calculate_ma_deviation_and_change(result)
    
    # MACDの計算
    result = calculate_macd(result)
    
    # RSIの計算
    result = calculate_rsi(result)
    
    # RCIの計算
    result = calculate_rci(result)
    
    # ボリンジャーバンドの計算
    result = calculate_bollinger_bands(result)
    
    # ボリンジャーバンドの詳細位置分析
    result = calculate_bollinger_band_position(result)
    
    # 一目均衡表の計算
    result = calculate_ichimoku(result)
    
    # 取引シグナルの計算 (MACD-RSI)
    result = calculate_trading_signals_MACD_RSI(result)
    
    # 新しい取引シグナルの計算 (MACD-RCI)
    result = calculate_trading_signals_MACD_RCI(result)
    
    # 移動平均線乖離率に基づく取引シグナルの計算
    result = calculate_trading_signals_MA_Deviation(result)
    
    # ボリンジャーバンドに基づく取引シグナルの計算
    result = calculate_trading_signals_bollinger(result)
    
    # ボリンジャーバンド（20SMA）とMACDを組み合わせた取引シグナルの計算
    result = calculate_trading_signals_BB_MACD(result)
    
    # ボリンジャーバンド（20SMA）とMACDの詳細な取引シグナル分析
    result = calculate_trading_signals_BB_MACD_detailed(result)
    
    # すべての指標が計算された結果を返す
    return result

def extract_BB_MACD_signals(is_test_mode: bool = False) -> Dict[str, List[Dict]]:
    """
    BB-MACDシグナルに基づいて買い・売り銘柄を抽出します
    
    Args:
        is_test_mode: テストモードかどうか
        
    Returns:
        Dict[str, List[Dict]]: 買い・売り銘柄のリストを含む辞書
    """
    import config
    import os
    
    # ロガーを取得
    logger = logging.getLogger("StockSignal")
    
    # テストモードに応じてディレクトリを設定（extract_signals.pyと同じ構造に変更）
    if is_test_mode:
        input_dir = os.path.join(config.TEST_DIR, "StockSignal", "TechnicalSignal")  # テクニカル指標入力ディレクトリ
        output_dir = os.path.join(config.TEST_DIR, "Result")  # extract_signals.pyと同じ出力先
    else:
        input_dir = os.path.join(config.BASE_DIR, "StockSignal", "TechnicalSignal")       # テクニカル指標入力ディレクトリ  
        output_dir = os.path.join(config.BASE_DIR, "StockSignal", "Result")  # extract_signals.pyと同じ出力先
    
    # 出力ディレクトリが存在しない場合は作成
    os.makedirs(output_dir, exist_ok=True)
    
    # 結果を格納する辞書
    results = {
        'buy_signals': [],
        'sell_signals': []
    }
    
    try:
        # 最新シグナルファイルを読み込み
        latest_signal_file = os.path.join(input_dir, config.LATEST_SIGNAL_FILE)
        
        if not os.path.exists(latest_signal_file):
            logger.error(f"最新シグナルファイルが見つかりません: {latest_signal_file}")
            return results
        
        # CSVファイルを読み込み
        df = pd.read_csv(latest_signal_file, index_col=0, parse_dates=True)
        
        # 会社名・テーママッピングを取得
        company_info_map = get_company_info_map(is_test_mode)
        
        # 高値と安値の中間値（ミッドポイント）を計算
        df['Midpoint'] = (df['High'] + df['Low']) / 2
        
        # BB-MACDシグナルに基づいて銘柄を抽出
        buy_stocks = []
        sell_stocks = []
        
        # 買いシグナルの抽出（Close > Midpoint条件付き）
        bb_macd_buy_signals = df[(df['BB-MACD'] == 'Buy') & (df['Close'] > df['Midpoint'])]
        
        for index, row in bb_macd_buy_signals.iterrows():
            ticker = row.get('Ticker', '')
            company_info = company_info_map.get(str(ticker), {'company': '', 'theme': ''})
            company = row.get('Company', company_info.get('company', ''))
            theme = company_info.get('theme', '')
            
            # 基本的な株価情報のみを抽出（不要な列を除外）
            close = row.get('Close', 0.0)
            bb_middle = row.get('BB_Middle', 0.0)
            macd = row.get('MACD', 0.0)
            
            stock_info = {
                'Ticker': ticker,
                'Company': company,
                'Theme': theme,
                'Close': close,
                'MACD': macd,
                'BB_Middle_20SMA': bb_middle
            }
            buy_stocks.append(stock_info)
        
        # 売りシグナルの抽出（Close < Midpoint条件付き）
        bb_macd_sell_signals = df[(df['BB-MACD'] == 'Sell') & (df['Close'] < df['Midpoint'])]
        
        for index, row in bb_macd_sell_signals.iterrows():
            ticker = row.get('Ticker', '')
            company_info = company_info_map.get(str(ticker), {'company': '', 'theme': ''})
            company = row.get('Company', company_info.get('company', ''))
            theme = company_info.get('theme', '')
            
            # 基本的な株価情報のみを抽出（不要な列を除外）
            close = row.get('Close', 0.0)
            bb_middle = row.get('BB_Middle', 0.0)
            macd = row.get('MACD', 0.0)
            
            stock_info = {
                'Ticker': ticker,
                'Company': company,
                'Theme': theme,
                'Close': close,
                'MACD': macd,
                'BB_Middle_20SMA': bb_middle
            }
            sell_stocks.append(stock_info)
        
        # 結果を辞書に格納
        results['buy_signals'] = buy_stocks
        results['sell_signals'] = sell_stocks
        
        # CSVファイルとして出力（日付なし、不要な列を除外）
        # 買いシグナル銘柄をCSVに出力（該当銘柄がない場合も空ファイルを出力）
        buy_output_file = os.path.join(output_dir, 'bb_macd_buy_signals.csv')
        if buy_stocks:
            buy_df = pd.DataFrame(buy_stocks)
            
            # 数値データの小数点以下桁数を調整
            buy_df['MACD'] = buy_df['MACD'].round(2)
            buy_df['BB_Middle_20SMA'] = buy_df['BB_Middle_20SMA'].round(2)
            
            # 終値の表示形式を調整（小数点以下が0の場合は整数表示、それ以外は小数点以下1桁）
            buy_df['Close'] = buy_df['Close'].apply(
                lambda x: int(x) if x == int(x) else round(x, 1)
            )
            
            # カラム名を日本語に変更（20SMAに短縮）
            buy_df = buy_df.rename(columns={
                'Close': '終値',
                'MACD': 'MACD',
                'BB_Middle_20SMA': '20SMA'
            })
            
            buy_df.to_csv(buy_output_file, index=False, encoding='utf-8-sig')
            logger.info(f"BB-MACD買いシグナル銘柄 {len(buy_stocks)}社をCSVに出力しました: {buy_output_file}")
        else:
            # 該当銘柄がない場合は空のデータフレームを作成して出力
            empty_buy_df = pd.DataFrame(columns=['Ticker', 'Company', 'Theme', '終値', 'MACD', '20SMA'])
            empty_buy_df.to_csv(buy_output_file, index=False, encoding='utf-8-sig')
            logger.info(f"BB-MACD買いシグナル銘柄 0社（空ファイル）をCSVに出力しました: {buy_output_file}")
        
        # 売りシグナル銘柄をCSVに出力
        sell_output_file = os.path.join(output_dir, 'bb_macd_sell_signals.csv')
        if sell_stocks:
            sell_df = pd.DataFrame(sell_stocks)
            
            # 数値データの小数点以下桁数を調整
            sell_df['MACD'] = sell_df['MACD'].round(2)
            sell_df['BB_Middle_20SMA'] = sell_df['BB_Middle_20SMA'].round(2)
            
            # 終値の表示形式を調整（小数点以下が0の場合は整数表示、それ以外は小数点以下1桁）
            sell_df['Close'] = sell_df['Close'].apply(
                lambda x: int(x) if x == int(x) else round(x, 1)
            )
            
            # カラム名を日本語に変更（20SMAに短縮）
            sell_df = sell_df.rename(columns={
                'Close': '終値',
                'MACD': 'MACD',
                'BB_Middle_20SMA': '20SMA'
            })
            
            sell_df.to_csv(sell_output_file, index=False, encoding='utf-8-sig')
            logger.info(f"BB-MACD売りシグナル銘柄 {len(sell_stocks)}社をCSVに出力しました: {sell_output_file}")
        else:
            # 該当銘柄がない場合は空のデータフレームを作成して出力
            empty_sell_df = pd.DataFrame(columns=['Ticker', 'Company', 'Theme', '終値', 'MACD', '20SMA'])
            empty_sell_df.to_csv(sell_output_file, index=False, encoding='utf-8-sig')
            logger.info(f"BB-MACD売りシグナル銘柄 0社（空ファイル）をCSVに出力しました: {sell_output_file}")
        
        # サマリー情報をログに出力
        logger.info(f"BB-MACDシグナル抽出結果:")
        logger.info(f"  買いシグナル: {len(buy_stocks)}社")
        logger.info(f"  売りシグナル: {len(sell_stocks)}社")
        logger.info(f"  出力先ディレクトリ: {output_dir}")
        
        # 詳細情報をログに出力（最初の5社まで）
        if buy_stocks:
            logger.info("買いシグナル銘柄（上位5社）:")
            for i, stock in enumerate(buy_stocks[:5]):
                logger.info(f"  {i+1}. {stock['Ticker']} {stock['Company']} ({stock['Theme']}) "
                           f"(終値: {stock['Close']}, MACD: {stock['MACD']:.2f}, "
                           f"20SMA: {stock['BB_Middle_20SMA']:.2f})")
        
        if sell_stocks:
            logger.info("売りシグナル銘柄（上位5社）:")
            for i, stock in enumerate(sell_stocks[:5]):
                logger.info(f"  {i+1}. {stock['Ticker']} {stock['Company']} ({stock['Theme']}) "
                           f"(終値: {stock['Close']}, MACD: {stock['MACD']:.2f}, "
                           f"20SMA: {stock['BB_Middle_20SMA']:.2f})")
        
    except Exception as e:
        logger.error(f"BB-MACDシグナル抽出中にエラーが発生しました: {str(e)}")
    
    return results


def get_BB_MACD_signal_summary(is_test_mode: bool = False) -> Dict:
    """
    BB-MACDシグナルのサマリー統計を取得します
    
    Args:
        is_test_mode: テストモードかどうか
        
    Returns:
        Dict: サマリー統計情報
    """
    import config
    import os
    
    # ロガーを取得
    logger = logging.getLogger("StockSignal")
    
    # テストモードに応じて入力ディレクトリを設定（config.pyの設定に従う）
    if is_test_mode:
        input_dir = config.TEST_TECHNICAL_DIR  # テクニカル指標入力ディレクトリ
    else:
        input_dir = config.TECHNICAL_DIR       # テクニカル指標入力ディレクトリ
    
    # サマリー統計を格納する辞書
    summary = {
        'total_stocks': 0,
        'buy_signals': 0,
        'sell_signals': 0,
        'no_signal': 0,
        'bb_condition_only': 0,
        'macd_condition_only': 0,
        'both_conditions': 0,
        'buy_signal_rate': 0.0,
        'sell_signal_rate': 0.0,
        'signal_rate': 0.0
    }
    
    try:
        # 最新シグナルファイルを読み込み
        latest_signal_file = os.path.join(input_dir, config.LATEST_SIGNAL_FILE)
        
        if not os.path.exists(latest_signal_file):
            logger.error(f"最新シグナルファイルが見つかりません: {latest_signal_file}")
            return summary
        
        # CSVファイルを読み込み
        df = pd.read_csv(latest_signal_file, index_col=0, parse_dates=True)
        
        # 統計計算
        total_stocks = len(df)
        buy_signals = len(df[df['BB-MACD'] == 'Buy'])
        sell_signals = len(df[df['BB-MACD'] == 'Sell'])
        no_signal = total_stocks - buy_signals - sell_signals
        
        # 条件別の分析（詳細データがある場合）
        bb_condition_only = 0
        macd_condition_only = 0
        both_conditions = 0
        
        if 'BB_Condition' in df.columns and 'MACD_Condition' in df.columns:
            bb_only = df[(df['BB_Condition'] == True) & (df['MACD_Condition'] == False)]
            macd_only = df[(df['BB_Condition'] == False) & (df['MACD_Condition'] == True)]
            both = df[(df['BB_Condition'] == True) & (df['MACD_Condition'] == True)]
            
            bb_condition_only = len(bb_only)
            macd_condition_only = len(macd_only)
            both_conditions = len(both)
        
        # 割合の計算
        buy_signal_rate = (buy_signals / total_stocks * 100) if total_stocks > 0 else 0
        sell_signal_rate = (sell_signals / total_stocks * 100) if total_stocks > 0 else 0
        signal_rate = ((buy_signals + sell_signals) / total_stocks * 100) if total_stocks > 0 else 0
        
        # サマリー辞書を更新
        summary.update({
            'total_stocks': total_stocks,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'no_signal': no_signal,
            'bb_condition_only': bb_condition_only,
            'macd_condition_only': macd_condition_only,
            'both_conditions': both_conditions,
            'buy_signal_rate': buy_signal_rate,
            'sell_signal_rate': sell_signal_rate,
            'signal_rate': signal_rate
        })
        
        # サマリー情報をログに出力
        logger.info("=== BB-MACDシグナル サマリー統計 ===")
        logger.info(f"総銘柄数: {total_stocks}")
        logger.info(f"買いシグナル: {buy_signals}社 ({buy_signal_rate:.1f}%)")
        logger.info(f"売りシグナル: {sell_signals}社 ({sell_signal_rate:.1f}%)")
        logger.info(f"シグナルなし: {no_signal}社 ({100-signal_rate:.1f}%)")
        logger.info(f"全体シグナル発生率: {signal_rate:.1f}%")
        
        if bb_condition_only + macd_condition_only + both_conditions > 0:
            logger.info("=== 条件別分析 ===")
            logger.info(f"BB条件のみ満たす: {bb_condition_only}社")
            logger.info(f"MACD条件のみ満たす: {macd_condition_only}社")
            logger.info(f"両条件満たす（シグナル発生）: {both_conditions}社")
        
    except Exception as e:
        logger.error(f"BB-MACDサマリー統計計算中にエラーが発生しました: {str(e)}")
    
    return summary

def process_data_for_ticker(ticker: str, data_dir: str, output_dir: str) -> Tuple[bool, Optional[pd.DataFrame]]:
    """
    特定の銘柄のデータを処理し、テクニカル指標を計算してCSVに保存します
    
    Args:
        ticker: 銘柄コード
        data_dir: データが保存されているディレクトリ
        output_dir: 出力先ディレクトリ
        
    Returns:
        Tuple[bool, Optional[pd.DataFrame]]: 処理が成功したかどうかと、最新の指標データ
    """
    # ロガーを取得（ロギング設定はアプリケーション起動時に行われている前提）
    logger = logging.getLogger("StockSignal")
    
    try:
        # ファイルパスの作成
        # 入力ファイル: データディレクトリ内の銘柄コード.csv（例: 7203.csv）
        input_file = os.path.join(data_dir, f"{ticker}.csv")
        # 出力ファイル: 出力ディレクトリ内の銘柄コード_signal.csv（例: 7203_signal.csv）
        output_file = os.path.join(output_dir, f"{ticker}_signal.csv")
        # 最新データ出力ファイル: 出力ディレクトリ内の銘柄コード_latest_signal.csv
        latest_output_file = os.path.join(output_dir, f"{ticker}_latest_signal.csv")
        
        # 入力ファイルの存在確認
        # ファイルが見つからない場合は処理をスキップ
        if not os.path.exists(input_file):
            logger.warning(f"銘柄 {ticker} のデータファイルが見つかりません: {input_file}")
            return False, None
        
        # データの読み込み
        # index_col=0: 最初の列をインデックスとして使用
        # parse_dates=True: インデックスを日付型として解析
        df = pd.read_csv(input_file, index_col=0, parse_dates=True)
        
        # データの有効性確認：空データチェック
        # データフレームが空の場合は処理をスキップ
        if df.empty:
            logger.warning(f"銘柄 {ticker} のデータが空です")
            return False, None
        
        # データの有効性確認：インデックスが日付型かチェック
        # テクニカル指標計算には日付型インデックスが必要
        if not isinstance(df.index, pd.DatetimeIndex):
            logger.warning(f"銘柄 {ticker} のインデックスが日付型ではありません")
            return False, None
        
        # データの有効性確認：必要なカラムの存在チェック
        # OHLCV（始値、高値、安値、終値、出来高）がすべて必要
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.warning(f"銘柄 {ticker} のデータに必要なカラムがありません: {missing_columns}")
            return False, None
        
        # データ型の変換：TALibはfloat64（double）型を要求するため、OHLCVカラムを明示的にfloat64に変換
        # CSVから読み込んだデータがint型やobject型のままになっている可能性がある
        for col in required_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('float64')
        
        # 欠損値の処理
        # 前方埋め（直前の有効な値で埋める）と後方埋め（直後の有効な値で埋める）を組み合わせて処理
        df = df.fillna(method='ffill').fillna(method='bfill')
        
        # データ数の確認とログ出力
        logger.info(f"銘柄 {ticker} のデータ数: {len(df)}行")
        
        # テクニカル指標の計算（メイン処理）
        # すべてのテクニカル指標を計算して新しいデータフレームを取得
        signal_df = calculate_all_indicators(df)
        
        # 銘柄コードを列として追加（後で複数銘柄をまとめる際に必要）
        signal_df['Ticker'] = ticker
        
        # すべてのデータをCSVに保存（全期間の詳細データ）
        signal_df.to_csv(output_file)
        logger.info(f"銘柄 {ticker} のテクニカル指標（全データ）を計算・保存しました")
        
        # 最新の日付のデータのみを抽出（データフレームの最終行）
        # .copy()で新しいデータフレームを作成（警告回避）
        latest_data = signal_df.iloc[-1:].copy()
        
        # NaN（欠損値）の確認
        # データフレーム内に欠損値を含む列があるかチェック
        nan_columns = latest_data.columns[latest_data.isna().any()].tolist()
        if nan_columns:
            logger.warning(f"銘柄 {ticker} の最新データにNaN値があります: {nan_columns}")
            # NaNを適切な値で埋める（文字列カラムは空文字、数値カラムは0）
            for col in nan_columns:
                # シグナルや状態を表す列は空文字で埋める
                if col == 'Signal' or col == 'Ichimoku_SanYaku' or col == 'Ichimoku_Cloud_Status':
                    latest_data[col] = latest_data[col].fillna('')
                else:
                    # それ以外の列（数値データ）は0で埋める
                    latest_data[col] = latest_data[col].fillna(0)
        
        # 最新データのみを別ファイルに保存（最新日の状態のみ）
        latest_data.to_csv(latest_output_file)
        logger.info(f"銘柄 {ticker} の最新テクニカル指標を保存しました")
        
        # 処理成功フラグと最新データを返す
        return True, latest_data
        
    except Exception as e:
        # 処理中の例外をキャッチしてログに記録
        logger.error(f"銘柄 {ticker} のテクニカル指標計算中にエラーが発生しました: {str(e)}")
        # 処理失敗フラグとNoneを返す
        return False, None


def get_company_info_map(is_test_mode: bool = False) -> Dict[str, Dict[str, str]]:
    """
    銘柄コードから会社名とテーマへのマッピングを取得します
    
    Args:
        is_test_mode: テストモードかどうか
        
    Returns:
        Dict[str, Dict[str, str]]: 銘柄コードをキー、{'company': 会社名, 'theme': テーマ}を値とする辞書
    """
    import config  # 設定値を取得するために設定モジュールをインポート
    
    # ロガーを取得
    logger = logging.getLogger("StockSignal")
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


def calculate_signals(tickers: List[str], is_test_mode: bool = False) -> Dict[str, bool]:
    """
    複数の銘柄に対してテクニカル指標を計算します
    
    Args:
        tickers: 銘柄コードのリスト
        is_test_mode: テストモードかどうか
        
    Returns:
        Dict[str, bool]: 銘柄コードをキー、成功したかどうかを値とする辞書
    """
    import config  # 設定値を取得するために設定モジュールをインポート
    
    # ロガーを取得
    logger = logging.getLogger("StockSignal")
    # 各銘柄の処理結果を格納する辞書を初期化
    results = {}
    # 全銘柄の最新シグナルデータを格納するリストを初期化
    all_latest_signals = []
    # 削除対象の一時ファイルパスを格納するリストを初期化
    temp_files_to_remove = []
    
    # テストモードに応じて入力ディレクトリを設定
    # 株価データが保存されているディレクトリを指定
    data_dir = config.TEST_RESULT_DIR if is_test_mode else config.RESULT_DIR
    
    # テストモードに応じて出力ディレクトリを設定
    # テクニカル指標の計算結果を保存するディレクトリを指定
    if is_test_mode:
        output_dir = os.path.join(config.TEST_DIR, "StockSignal", "TechnicalSignal")
    else:
        output_dir = os.path.join(config.BASE_DIR, "StockSignal", "TechnicalSignal")
    
    # 出力先ディレクトリが存在しない場合は作成
    # exist_ok=True で既に存在する場合はエラーにしない
    os.makedirs(output_dir, exist_ok=True)
    
    # 処理開始のログを出力
    logger.info(f"テクニカル指標の計算を開始します。対象企業数: {len(tickers)}")
    
    # 銘柄コードから会社情報（会社名・テーマ）へのマッピングを取得
    # 最終結果に会社名とテーマを表示するために使用
    company_info_map = get_company_info_map(is_test_mode)
    
    # 各銘柄に対して処理を実行
    for ticker in tickers:
        # 個別銘柄の処理実行
        # 戻り値: 成功フラグと最新日の指標データ
        success, latest_data = process_data_for_ticker(ticker, data_dir, output_dir)
        # 処理結果を辞書に記録
        results[ticker] = success
        
        # 処理が成功し、最新データが取得できた場合
        if success and latest_data is not None:
            # 会社情報を追加（マッピングに存在しない場合は空文字）
            company_info = company_info_map.get(ticker, {'company': '', 'theme': ''})
            latest_data['Company'] = company_info.get('company', '')
            latest_data['Theme'] = company_info.get('theme', '')
            
            # 結合用リストに追加（後で全銘柄のデータを1つのファイルにまとめるため）
            all_latest_signals.append(latest_data)
            
            # 削除対象の一時ファイルパスをリストに追加
            latest_output_file = os.path.join(output_dir, f"{ticker}_latest_signal.csv")
            temp_files_to_remove.append(latest_output_file)
    
    # 処理結果のサマリーをログに出力
    # 成功・失敗した銘柄数をカウント
    success_count = sum(1 for v in results.values() if v)
    logger.info(f"テクニカル指標の計算が完了しました。成功: {success_count}社, 失敗: {len(results) - success_count}社")
    
    # 全企業の最新テクニカル指標を一つのファイルにまとめる
    if all_latest_signals:  # 少なくとも1つの成功した銘柄がある場合
        try:
            # 全銘柄のデータフレームを結合（縦方向に結合）
            combined_df = pd.concat(all_latest_signals, axis=0)
            
            # Ticker（銘柄コード）、Company（会社名）、Theme（テーマ）を先頭列に移動
            # 見やすさを優先したカラム順序に変更
            cols = ['Ticker', 'Company', 'Theme'] + [col for col in combined_df.columns if col not in ['Ticker', 'Company', 'Theme']]
            combined_df = combined_df[cols]
            
            # 結合したデータを保存
            # ファイル名をクリーンアップして使用（余分な空白などを除去）
            output_filename = config.LATEST_SIGNAL_FILE.strip()
            combined_output_file = os.path.join(output_dir, output_filename)
            
            # 保存処理のログを出力
            logger.info(f"全企業の最新テクニカル指標を {output_filename} に保存します: {combined_output_file}")
            # インデックス付きでCSVに保存（通常は日付がインデックス）
            combined_df.to_csv(combined_output_file, index=True)
            # 保存完了のログを出力
            logger.info(f"全企業の最新テクニカル指標を {output_filename} にまとめました")
            
            # 一時ファイルの削除処理を実行
            files_removed = 0
            for file_path in temp_files_to_remove:
                try:
                    # ファイルの存在確認
                    if os.path.exists(file_path):
                        # ファイルを削除
                        os.remove(file_path)
                        files_removed += 1
                except Exception as e:
                    # ファイル削除時のエラーをログに記録（処理は継続）
                    logger.warning(f"一時ファイルの削除中にエラーが発生しました: {file_path}, エラー: {str(e)}")
            
            # 削除処理結果をログに出力
            logger.info(f"一時ファイル {files_removed}/{len(temp_files_to_remove)} 件を削除しました")
            
        except Exception as e:
            # 統合ファイル作成時の例外をキャッチしてログに記録
            logger.error(f"テクニカル指標の統合ファイル作成中にエラーが発生しました: {str(e)}")
    
    # 処理結果の辞書を返す
    return results