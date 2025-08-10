import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
import os

def test_candlestick_colors():
    """Ticker 2201のローソク足の色をテスト"""
    
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

