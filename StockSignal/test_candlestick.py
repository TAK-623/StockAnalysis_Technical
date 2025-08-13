"""
ローソク足チャートテストモジュール - チャート生成機能の動作確認

このモジュールは、ローソク足チャートの生成機能をテストするためのスクリプトです。
特定の銘柄（2201）のデータを使用して、ローソク足の色設定やチャート生成の
動作を確認します。

主な機能：
- ローソク足の色設定テスト（陽線：赤色、陰線：青色）
- mplfinanceライブラリを使用したチャート生成テスト
- 移動平均線と出来高の表示確認
- 日本語フォント対応の確認
"""
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
import os

def test_candlestick_colors():
    """
    Ticker 2201のローソク足の色をテスト
    
    指定銘柄の株価データを読み込み、ローソク足の色設定を確認し、
    テスト用チャートを生成します。陽線は赤色、陰線は青色で表示されます。
    
    テスト内容：
    1. 最新5日分のデータ表示（Open/Close値と色判定）
    2. mplfinanceを使用したローソク足チャート生成
    3. 移動平均線（5日・25日）の表示
    4. 出来高の表示
    5. カスタムカラー設定の適用確認
    """
    
    # データを読み込み
    signal_file = os.path.join("TechnicalSignal", "2201_signal.csv")
    df = pd.read_csv(signal_file, encoding='utf-8')
    
    # 最新の5日分のデータを表示
    print("最新の5日分のデータ:")
    recent_data = df[['Date', 'Open', 'High', 'Low', 'Close']].tail(5)
    for _, row in recent_data.iterrows():
        date = row['Date']
        open_price = row['Open']
        close_price = row['Close']
        color = "赤色（陽線）" if close_price > open_price else "青色（陰線）"
        print(f"{date}: Open={open_price:.1f}, Close={close_price:.1f} -> {color}")
    
    # mplfinance用にデータを準備
    df_mpf = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].tail(20)
    df_mpf['Date'] = pd.to_datetime(df_mpf['Date'])
    df_mpf = df_mpf.set_index('Date')
    
    # マーケットカラー設定
    mc = mpf.make_marketcolors(
        up='#d32f2f',      # 陽線（赤色）
        down='#1e88e5',    # 陰線（青色）
        edge='inherit',    # 枠線は継承
        volume='#666666',  # 出来高はグレー
        wick='inherit'     # ヒゲは継承
    )
    s = mpf.make_mpf_style(base_mpf_style='yahoo', marketcolors=mc)
    
    # チャートを生成
    mpf.plot(
        df_mpf,
        type='candle',
        mav=(5, 25),
        volume=True,
        style=s,
        title="2201 - テスト用ローソク足チャート",
        figsize=(12, 8),
        savefig="test_2201_chart.png"
    )
    
    print("\nチャートを test_2201_chart.png に保存しました。")

if __name__ == "__main__":
    test_candlestick_colors()

