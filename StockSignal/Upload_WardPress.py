"""
WordPress投稿モジュール - 株価分析結果の自動投稿・チャート生成

このスクリプトは、株価シグナル分析の結果をWordPressサイトに自動投稿します。
主な機能：
1. 投稿する各種CSVファイルを読み込み
2. CSVデータをHTML形式のテーブルに変換
3. WordPress REST APIを使用して記事を投稿
4. 記事内に展開可能なブロックとして表を表示
5. レンジブレイク銘柄のチャート自動生成
6. 日本語フォント対応のチャート出力

投稿内容：
- 各種売買シグナル銘柄一覧
- 強気/弱気トレンド銘柄一覧
- レンジブレイク銘柄一覧（チャート付き）
- 押し目銘柄一覧
- BB-MACDシグナル銘柄一覧
- 一目均衡表シグナル銘柄一覧

使用技術：
- WordPress REST API
- mplfinance（チャート生成）
- matplotlib（グラフ描画）
- japanize_matplotlib（日本語表示）
"""
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import base64
import japanize_matplotlib
import mplfinance as mpf
from io import BytesIO
import time
from matplotlib import font_manager as fm
from PIL import Image
import math
import yfinance as yf
from typing import Optional

# WordPressサイトの接続情報を設定
WP_SITE_URL = "https://www.takstorage.site/"  # WordPressサイトのURL
WP_API_ENDPOINT = f"{WP_SITE_URL}/wp-json/wp/v2/posts"  # WordPress REST API 投稿用エンドポイント
WP_USERNAME = "tak.note7120@gmail.com"  # WordPressの管理者ユーザー名（メールアドレス）
WP_APP_PASSWORD = "GNrk aQ3d 7GWu p1fw dCfM pAGH"  # WordPress アプリケーションパスワード（セキュリティ向上のため通常のパスワードではなくアプリパスワードを使用）

# 今日の日付と昨日の日付を取得（昨日の株価データを投稿するため）
current_date = (datetime.now()).strftime("%Y/%m/%d")  # YYYY/MM/DD形式

# チャート生成用の設定
# フォント設定とスタイル
plt.style.use('default')
japanize_matplotlib.japanize()
# 日本語フォントを確実に登録
possible_fonts = [
    r"C:\\Windows\\Fonts\\meiryo.ttc",
    r"C:\\Windows\\Fonts\\meiryob.ttc",
    r"C:\\Windows\\Fonts\\msgothic.ttc",
    r"C:\\Windows\\Fonts\\YuGothM.ttc"
]
for fpath in possible_fonts:
    if os.path.exists(fpath):
        try:
            fm.fontManager.addfont(fpath)
        except Exception:
            pass
plt.rcParams['font.family'] = ['Meiryo', 'Yu Gothic', 'MS Gothic']

# 投稿の冒頭部分のテキスト（HTMLタグ含む）
# 投稿の説明文と銘柄コードの解説を含む
intro_text = """
<p>{current_date}終わり時点での情報です。</p>
<p>Pythonを使用して自動でデータ収集&演算を行い、売買シグナルの出た銘柄、強いトレンドのある銘柄、レンジをブレイクした銘柄をそれぞれ抽出しています。</p>
<p>銘柄名に付いているアルファベットで市場を表しています。</p>
<div class="graybox">
<p>P: プライム市場の銘柄</p>
<p>S: スタンダード市場の銘柄</p>
<p>G: グロース市場の銘柄</p>
</div>
<p></p>
<p>シグナルはMACDとRSIをもとに算出したものと、MACDとRCIをもとに算出したもの、MACDとRSIとRCIをもとに算出したものの3種類を挙げています。</p>
<p>強いトレンド銘柄は買いトレンドと売りトレンドの両方の銘柄を挙げています。</p>
<p>レンジブレイク銘柄は、直近1か月の高値をブレイクした銘柄を挙げています。</p>
<p></p>
""".format(current_date=current_date)

def read_csv_to_html_table(csv_file_path):
    """
    CSVファイルを読み込み、スタイリングされたHTML表に変換します
    
    指定されたCSVファイルを読み込み、数値フォーマットを調整した上で
    HTMLテーブル形式に変換します。長いテキストに対応したスタイリングも適用します。
    
    Args:
        csv_file_path (str): 読み込むCSVファイルのパス
        
    Returns:
        tuple: (スタイル適用済みのHTML表（スクロール可能なコンテナ内）, 銘柄数)
    """
    # ファイルが存在しない場合の処理
    if not os.path.exists(csv_file_path):
        print(f"警告: ファイルが見つかりません: {csv_file_path}")
        return "<p>データが見つかりません</p>", 0
    
    # CSVファイルをpandasデータフレームとして読み込み
    df = pd.read_csv(csv_file_path)

    # 数値フォーマットをカスタマイズする関数
    def format_number(x):
        if pd.isna(x):  # NaN値の場合は処理しない
            return x
        
        try:
            # 数値に変換可能な場合
            num_value = float(x)
            # 整数かどうかをチェック
            if num_value.is_integer():
                return int(num_value)  # 整数の場合は整数として表示
            else:
                return f"{num_value:.1f}"  # 小数点以下がある場合は1桁まで表示
        except (ValueError, TypeError):
            # 数値に変換できない場合はそのまま返す
            return x

    # 各列のデータタイプを確認し、数値列に対してフォーマット適用
    for col in df.columns:
        # 数値列（intまたはfloat）のみを処理
        if df[col].dtype in ['int64', 'float64']:
            df[col] = df[col].apply(format_number)

    # DataFrame を HTML テーブルに変換
    # index=False: インデックスは表示しない
    # border=1: テーブル境界線を表示
    # escape=False: HTML特殊文字をエスケープしない（HTMLタグを使用可能に）
    df_html = df.to_html(index=False, border=1, escape=False)

    # 銘柄名（Name列）が長い場合でもテーブルレイアウトを崩さないようにスタイル適用
    # 列幅の最大値を制限し、長いテキストは折り返す
    df_html = df_html.replace('<th>', '<th style="max-width:800px; white-space:nowrap; overflow:hidden;">')
    df_html = df_html.replace('<td>', '<td style="max-width:800px; word-wrap:break-word;">')

    # テーブルをスクロール可能なdivコンテナでラップ
    # コンテンツが大きくても表示領域を固定できる
    styled_table = f"""
    <div class="scroll-box">
        {df_html}
    </div>
    """
    # テーブルの内容とCSV内の銘柄数（行数）を返す
    return styled_table, len(df)

def load_company_names():
    """
    銘柄名辞書を読み込み
    
    Returns:
        dict: ティッカーをキー、銘柄名を値とする辞書
    """
    try:
        company_list_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "company_list_20250426.csv")
        df = pd.read_csv(company_list_file, encoding='utf-8')
        return dict(zip(df['Ticker'], df['銘柄名']))
    except Exception as e:
        print(f"銘柄名ファイルの読み込みエラー: {e}")
        return {}

def get_roe_for_ticker(ticker: str) -> Optional[float]:
    """
    指定された銘柄のROE情報をyfinanceから取得
    
    Args:
        ticker: 銘柄コード（例: "7203.T"）
    
    Returns:
        ROE値（パーセンテージ）、取得できない場合はNone
    """
    try:
        # 日本株の場合は.Tを付ける
        if not ticker.endswith('.T'):
            ticker_with_suffix = f"{ticker}.T"
        else:
            ticker_with_suffix = ticker
        
        # yfinanceでティッカー情報を取得
        stock = yf.Ticker(ticker_with_suffix)
        
        # 基本情報からROEを直接取得
        info = stock.info
        roe = info.get('returnOnEquity')
        
        if roe is not None:
            # 小数形式をパーセンテージに変換
            roe_percentage = roe * 100
            return round(roe_percentage, 2)
        else:
            return None
            
    except Exception as e:
        print(f"{ticker}: ROE取得中にエラーが発生しました: {str(e)}")
        return None

def load_stock_data(ticker):
    """
    指定されたティッカーの株価データを読み込み
    
    Args:
        ticker (str): ティッカー
        
    Returns:
        pandas.DataFrame: 株価データ（Date, Open, High, Low, Close, Volume）
    """
    try:
        technical_signal_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "TechnicalSignal")
        signal_file = os.path.join(technical_signal_dir, f"{ticker}_signal.csv")
        if not os.path.exists(signal_file):
            print(f"信号ファイルが見つかりません: {signal_file}")
            return None
        
        df = pd.read_csv(signal_file, encoding='utf-8')
        
        # 必要な列のみを選択
        required_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_columns):
            print(f"必要な列が見つかりません: {ticker}")
            return None
        
        # 日付列をdatetime型に変換
        df['Date'] = pd.to_datetime(df['Date'])
        
        # 最新のデータから過去6ヶ月分（全データ）を取得
        df = df.sort_values('Date')
        
        return df[required_columns]
        
    except Exception as e:
        print(f"株価データの読み込みエラー ({ticker}): {e}")
        return None

def generate_chart(ticker, company_names):
    """
    指定されたティッカーのチャートを生成し、`StockSignal/Result/{Ticker}_chart.png` に保存
    
    Args:
        ticker (str): ティッカー
        company_names (dict): 銘柄名辞書
        
    Returns:
        str | None: 生成されたチャートPNGファイルのパス
    """
    try:
        # 株価データを読み込み
        df = load_stock_data(ticker)
        if df is None or df.empty:
            return None
        
        # 銘柄名を取得
        company_name = company_names.get(ticker, f"銘柄{ticker}")
        
        # ROE情報を取得して「☆」マークを追加
        roe = get_roe_for_ticker(ticker)
        if roe is not None and roe >= 10.0:
            company_name += ' ☆'
        
        # mplfinance 形式に変換
        df_mpf = df.copy()
        df_mpf = df_mpf.set_index('Date')
        df_mpf = df_mpf[['Open', 'High', 'Low', 'Close', 'Volume']]

        # マーケットカラーとスタイル（日本語フォント）
        # mplfinanceでは、up=陽線（Close > Open）、down=陰線（Close < Open）
        # 日本式：赤=上昇、青=下降
        mc = mpf.make_marketcolors(
            up='#d32f2f',      # 陽線（赤色）
            down='#1e88e5',    # 陰線（青色）
            edge='inherit',    # 枠線は継承
            volume='inherit',  # 出来高は陽線・陰線と同じ色
            wick='inherit',    # ヒゲは継承
            ohlc='inherit'     # OHLCは継承
        )
        # 日本式スタイルを明示的に設定
        s = mpf.make_mpf_style(
            base_mpf_style='yahoo',
            marketcolors=mc,
            rc={'font.family': 'Meiryo'},
            y_on_right=True  # Y軸を右側に
        )

        # 出力ファイルパス
        result_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Result")
        os.makedirs(result_dir, exist_ok=True)
        output_file = os.path.join(result_dir, f"{ticker}_chart.png")

        # 画像をファイルに保存（figを受け取り軸を整形）
        fig, axes = mpf.plot(
            df_mpf,
            type='candle',
            mav=(5, 25),
            style=s,
            title=f"{ticker} - {company_name}",
            figsize=(9.6, 6.4),  # 960px × 640px (96 DPI)
            volume=True,  # 出来高を表示
            tight_layout=True,
            returnfig=True
        )
        # 出来高軸の指数表記オフ＋桁区切り
        try:
            from matplotlib.ticker import FuncFormatter
            if isinstance(axes, dict) and 'volume' in axes:
                axes['volume'].yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x):,}" if x >= 1 else f"{x}"))
            elif hasattr(fig, 'axes') and len(fig.axes) >= 2:
                fig.axes[-1].yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x):,}" if x >= 1 else f"{x}"))
        except Exception:
            pass
        
        # 軸ラベルを日本語に変更
        try:
            if isinstance(axes, dict):
                if 'main' in axes:
                    axes['main'].set_ylabel('価格', fontsize=10)
                if 'volume' in axes:
                    axes['volume'].set_ylabel('出来高', fontsize=10)
            elif hasattr(fig, 'axes') and len(fig.axes) >= 2:
                fig.axes[0].set_ylabel('価格', fontsize=10)
                fig.axes[1].set_ylabel('出来高', fontsize=10)
        except Exception:
            pass
        fig.savefig(output_file, dpi=300, bbox_inches='tight', format='png')
        plt.close(fig)
        return output_file
        
    except Exception as e:
        print(f"チャート生成エラー ({ticker}): {e}")
        return None

def upload_image_to_wordpress(image_path: str):
    """
    画像ファイルをWordPressメディアにアップロードしてURLを返す
    """
    try:
        media_endpoint = f"{WP_SITE_URL}/wp-json/wp/v2/media"
        # multipart/form-data で送信し、User-Agent を指定
        ua = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
        }
        files = {
            'file': (os.path.basename(image_path), open(image_path, 'rb'), 'image/png')
        }
        # 軽いリトライ（WAF対策）
        for attempt in range(5):
            resp = requests.post(media_endpoint, headers=ua, files=files, auth=HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD))
            if resp.status_code in (200, 201):
                return resp.json().get('source_url')
            # 403や429などは待機して再試行
            if resp.status_code in (403, 429, 500, 502, 503):
                time.sleep(2 + attempt * 2)
                continue
            break
        print(f"画像アップロード失敗: {resp.status_code} {resp.text}")
        return None
    except Exception as e:
        print(f"画像アップロードでエラー: {e}")
        return None

def post_to_wordpress(title, post_content):
    """
    WordPressに投稿記事を送信します
    
    Args:
        title (str): 投稿のタイトル
        post_content (str): 投稿の本文（HTMLフォーマット）
        
    Returns:
        None: 結果はコンソールに出力されます
    """
    # 投稿データの構成
    post_data = {
        "title": title,             # 記事タイトル
        "content": post_content,    # 記事本文（HTML）
        "status": "publish",        # 公開ステータス（下書き="draft"）
        "categories": [22],         # カテゴリーID（22=株価情報カテゴリー）
        "tags": [19],               # タグID（19=株価情報タグ）
        "featured_media": 809       # アイキャッチ画像ID
    }
    
    # WordPress REST APIにリクエストを送信
    # HTTPBasicAuth: ユーザー名とアプリパスワードで認証
    response = requests.post(
        WP_API_ENDPOINT,
        json=post_data,
        auth=HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD)
    )
    
    # レスポンスを確認して結果をコンソールに表示
    if response.status_code == 201:  # 201 Created = 投稿成功
        print("投稿が成功しました:", response.json()["link"])
    else:
        print("投稿に失敗しました:", response.status_code, response.text)

def combine_charts(chart_paths, charts_per_image=10):
    """
    複数のチャート画像を10銘柄ずつに分割して複数の画像ファイルを作成します。
    960px幅のグリッドレイアウトで配置します。
    
    Args:
        chart_paths (list of str): 結合するチャート画像のパスのリスト
        charts_per_image (int): 1つの画像ファイルに含めるチャート数（デフォルト10）
        
    Returns:
        list: 結合された画像のパスのリスト
    """
    if not chart_paths:
        return []

    # 画像を読み込む
    images = [Image.open(p) for p in chart_paths]
    
    # 目標幅（960px）
    target_width = 960
    
    # 各画像のサイズを取得
    original_widths, original_heights = zip(*(i.size for i in images))
    
    # 1行あたりの画像数を計算（960px幅に収まるように）
    # 各画像の幅を960pxで割って、1行に何個収まるかを計算
    avg_width = sum(original_widths) / len(original_widths)
    images_per_row = max(1, int(target_width / avg_width))
    
    # 画像をリサイズ（幅を統一）
    resized_images = []
    for img in images:
        # アスペクト比を保ってリサイズ
        aspect_ratio = img.size[1] / img.size[0]
        new_width = target_width // images_per_row
        new_height = int(new_width * aspect_ratio)
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        resized_images.append(resized_img)
    
    # 出力ファイルパス
    result_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Result")
    os.makedirs(result_dir, exist_ok=True)
    
    output_files = []
    
    # charts_per_imageずつに分割して画像を作成
    for i in range(0, len(resized_images), charts_per_image):
        batch_images = resized_images[i:i + charts_per_image]
        
        # グリッドの行数を計算
        num_rows = math.ceil(len(batch_images) / images_per_row)
        
        # 各行の高さを計算
        row_heights = []
        for row in range(num_rows):
            start_idx = row * images_per_row
            end_idx = min(start_idx + images_per_row, len(batch_images))
            row_height = max(img.size[1] for img in batch_images[start_idx:end_idx])
            row_heights.append(row_height)
        
        # 結合された画像のサイズを計算
        combined_width = target_width
        combined_height = sum(row_heights)
        
        # 結合された画像を作成
        combined_image = Image.new('RGB', (combined_width, combined_height), 'white')
        
        # 画像をグリッドレイアウトで配置
        y_offset = 0
        for row in range(num_rows):
            x_offset = 0
            row_height = row_heights[row]
            
            for col in range(images_per_row):
                img_idx = row * images_per_row + col
                if img_idx < len(batch_images):
                    img = batch_images[img_idx]
                    # 中央揃えで配置
                    x_center = x_offset + (target_width // images_per_row - img.size[0]) // 2
                    y_center = y_offset + (row_height - img.size[1]) // 2
                    combined_image.paste(img, (x_center, y_center))
                    x_offset += target_width // images_per_row
            
            y_offset += row_height
        
        # 画像を保存
        batch_num = i // charts_per_image + 1
        output_file = os.path.join(result_dir, f"combined_charts_batch_{batch_num}.png")
        combined_image.save(output_file, 'PNG')
        output_files.append(output_file)
    
    return output_files

def cleanup_old_charts():
    """
    Resultフォルダ内の古いチャート画像ファイル（.png）をすべて削除します
    """
    try:
        result_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Result")
        if os.path.exists(result_dir):
            # .pngファイルを検索して削除
            png_files = [f for f in os.listdir(result_dir) if f.endswith('.png')]
            deleted_count = 0
            
            for png_file in png_files:
                file_path = os.path.join(result_dir, png_file)
                try:
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"古いチャートファイルを削除: {png_file}")
                except Exception as e:
                    print(f"ファイル削除エラー ({png_file}): {e}")
            
            print(f"古いチャートファイル {deleted_count} 件を削除しました")
        else:
            print("Resultフォルダが見つかりません")
    except Exception as e:
        print(f"古いチャートファイルの削除中にエラーが発生しました: {e}")

def main():
    """
    メイン処理：CSVファイルの読み込み、HTML変換、WordPress投稿を実行
    """
    # 実行開始時に古いチャートファイルを削除
    print("古いチャートファイルの削除を開始します...")
    cleanup_old_charts()
    print("古いチャートファイルの削除が完了しました")
    
    # 読み込むCSVファイルのパス
    # ここを変更：StockSignal → StockAnalysis_Technical
    macd_rsi_signal_buy_csv_file_path = "C:\\Users\\mount\\Git\\StockAnalysis_Technical\\StockSignal\\Result\\macd_rsi_signal_result_buy.csv"   # 買いシグナルCSV
    macd_rsi_signal_sell_csv_file_path = "C:\\Users\\mount\\Git\\StockAnalysis_Technical\\StockSignal\\Result\\macd_rsi_signal_result_sell.csv" # 売りシグナルCSV
    macd_rci_signal_buy_csv_file_path = "C:\\Users\\mount\\Git\\StockAnalysis_Technical\\StockSignal\\Result\\macd_rci_signal_result_buy.csv"   # 買いシグナルCSV
    macd_rci_signal_sell_csv_file_path = "C:\\Users\\mount\\Git\\StockAnalysis_Technical\\StockSignal\\Result\\macd_rci_signal_result_sell.csv" # 売りシグナルCSV
    macd_rsi_rci_signal_buy_csv_file_path = "C:\\Users\\mount\\Git\\StockAnalysis_Technical\\StockSignal\\Result\\macd_rsi_rci_signal_result_buy.csv"   # 買いシグナルCSV
    macd_rsi_rci_signal_sell_csv_file_path = "C:\\Users\\mount\\Git\\StockAnalysis_Technical\\StockSignal\\Result\\macd_rsi_rci_signal_result_sell.csv" # 売りシグナルCSV
    breakout_csv_file_path = "C:\\Users\\mount\\Git\\StockAnalysis_Technical\\StockSignal\\Result\\Breakout.csv" # ブレイク銘柄CSV
    strong_buying_csv_file_path = "C:\\Users\\mount\\Git\\StockAnalysis_Technical\\StockSignal\\Result\\strong_buying_trend.csv" # 強い買いトレンド銘柄抽出
    strong_selling_csv_file_path = "C:\\Users\\mount\\Git\\StockAnalysis_Technical\\StockSignal\\Result\\strong_selling_trend.csv" # 強い売りトレンド銘柄抽出
    bb_macd_buy_signals_csv_file_path = "C:\\Users\\mount\\Git\\StockAnalysis_Technical\\StockSignal\\Result\\macd_bb_signal_result_buy.csv" # BB-MACD買いシグナル銘柄抽出
    bb_macd_sell_signals_csv_file_path = "C:\\Users\\mount\\Git\\StockAnalysis_Technical\\StockSignal\\Result\\macd_bb_signal_result_sell.csv" # BB-MACD売りシグナル銘柄抽出
    push_mark_csv_file_path = "C:\\Users\\mount\\Git\\StockAnalysis_Technical\\StockSignal\\Result\\push_mark.csv" # 押し目狙い銘柄抽出
    
    # 各CSVファイルを読み込んで、銘柄コード(Ticker)列で昇順ソートして再保存
    # 表示時に銘柄コードでソートされた状態にするため
    for file_path in [macd_rsi_signal_buy_csv_file_path, macd_rsi_signal_sell_csv_file_path, macd_rci_signal_buy_csv_file_path, macd_rci_signal_sell_csv_file_path, macd_rsi_rci_signal_buy_csv_file_path, macd_rsi_rci_signal_sell_csv_file_path, macd_rsi_rci_signal_sell_csv_file_path, bb_macd_buy_signals_csv_file_path, bb_macd_sell_signals_csv_file_path]:
        df = pd.read_csv(file_path, encoding='utf-8')    # CSVファイルを読み込み
        df_sorted = df.sort_values(by='Ticker')          # Ticker列で昇順ソート
        df_sorted.to_csv(file_path, index=False, encoding='utf-8')  # ソート結果を上書き保存
    
    # CSVデータをHTML表に変換（各テーブルの銘柄数も取得）
    html_table_macd_rsi_buy, macd_rsi_buy_count = read_csv_to_html_table(macd_rsi_signal_buy_csv_file_path)   # 買いシグナルテーブル
    html_table_macd_rsi_sell, macd_rsi_sell_count = read_csv_to_html_table(macd_rsi_signal_sell_csv_file_path) # 売りシグナルテーブル
    html_table_macd_rci_buy, macd_rci_buy_count = read_csv_to_html_table(macd_rci_signal_buy_csv_file_path)   # 買いシグナルテーブル
    html_table_macd_rci_sell, macd_rci_sell_count = read_csv_to_html_table(macd_rci_signal_sell_csv_file_path) # 売りシグナルテーブル
    html_table_macd_rsi_rci_buy, macd_rsi_rci_buy_count = read_csv_to_html_table(macd_rsi_rci_signal_buy_csv_file_path)   # 買いシグナルテーブル
    html_table_macd_rsi_rci_sell, macd_rsi_rci_sell_count = read_csv_to_html_table(macd_rsi_rci_signal_sell_csv_file_path) # 売りシグナルテーブル
    # ブレイク銘柄ファイルのパスを動的に決定（Breakout.csvが存在しない場合はRange_Brake.csvを使用）
    breakout_file_path = breakout_csv_file_path
    if not os.path.exists(breakout_file_path):
        range_brake_path = breakout_csv_file_path.replace("Breakout.csv", "Range_Brake.csv")
        if os.path.exists(range_brake_path):
            breakout_file_path = range_brake_path
            print(f"Breakout.csvが見つからないため、Range_Brake.csvを使用します: {range_brake_path}")
    
    html_table_breakout, breakout_count = read_csv_to_html_table(breakout_file_path) # ブレイク銘柄テーブル
    html_table_strong_buying, strong_buying_count = read_csv_to_html_table(strong_buying_csv_file_path) # 強い買いトレンド銘柄テーブル
    html_table_strong_selling, strong_selling_count = read_csv_to_html_table(strong_selling_csv_file_path) # 強い売りトレンド銘柄テーブル
    html_table_bb_macd_buy, bb_macd_buy_count = read_csv_to_html_table(bb_macd_buy_signals_csv_file_path) # BB-MACD買いシグナル銘柄テーブル
    html_table_bb_macd_sell, bb_macd_sell_count = read_csv_to_html_table(bb_macd_sell_signals_csv_file_path) # BB-MACD売りシグナル銘柄テーブル
    html_table_push_mark, push_mark_count = read_csv_to_html_table(push_mark_csv_file_path) # 押し目狙い銘柄テーブル
    
    # 投稿のタイトルと内容を作成
    post_title = "売買シグナル_{current_date}".format(current_date=current_date)  # 投稿タイトル
    
    # 投稿本文のHTML構成
    # WordPressテーマ「AFFINGER」用のスライドボックスブロックを使用
    # 初期状態では折りたたまれており、クリックで展開される
    post_content = f"""
        {intro_text}
        <h2>MACD & RSIによる売買シグナル</h2>
        <p>MACDとRSIによるシグナルは下記の条件で導出しています。</p>
        [st-mybox title="買いシグナルの条件" webicon="st-svg-check-circle" color="#03A9F4" bordercolor="#B3E5FC" bgcolor="#E1F5FE" borderwidth="2" borderradius="5" titleweight="bold"]
        <ol>
        <li>MACDがMACDシグナルを上回っている</li>
        <li>RSI短期がRSI長期を上回っている</li>
        <li>RSI長期が40以下</li>
        </ol>
        [/st-mybox]
        [st-mybox title="売りシグナルの条件" webicon="st-svg-check-circle" color="#03A9F4" bordercolor="#B3E5FC" bgcolor="#E1F5FE" borderwidth="2" borderradius="5" titleweight="bold"]
        <ol>
        <li>MACDがMACDシグナルを下回っている</li>
        <li>RSI短期がRSI長期を下回っている</li>
        <li>RSI長期が60以上</li>
        </ol>
        [/st-mybox]
        <h3>買いシグナル銘柄（{macd_rsi_buy_count}銘柄）</h3>
        <p><!-- wp:st-blocks/st-slidebox --></p>
        <div class="wp-block-st-blocks-st-slidebox st-slidebox-c is-collapsed has-st-toggle-icon is-st-toggle-position-left is-st-toggle-icon-position-left" data-st-slidebox="">
        <p class="st-btn-open" data-st-slidebox-toggle=""><i class="st-fa st-svg-plus-thin" data-st-slidebox-icon="" data-st-slidebox-icon-collapsed="st-svg-plus-thin" data-st-slidebox-icon-expanded="st-svg-minus-thin" aria-hidden=""></i><span class="st-slidebox-btn-text" data-st-slidebox-text="" data-st-slidebox-text-collapsed="クリックして展開" data-st-slidebox-text-expanded="閉じる">クリックして下さい</span></p>
        <div class="st-slidebox" data-st-slidebox-content="">
        <div class="scroll-box">
        買いシグナルテーブル
        {html_table_macd_rsi_buy}
        </div>
        </div>
        </div>
        <p><!-- /wp:st-blocks/st-slidebox --></p>
        
        <h3>売りシグナル銘柄（{macd_rsi_sell_count}銘柄）</h3>
        <p><!-- wp:st-blocks/st-slidebox --></p>
        <div class="wp-block-st-blocks-st-slidebox st-slidebox-c is-collapsed has-st-toggle-icon is-st-toggle-position-left is-st-toggle-icon-position-left" data-st-slidebox="">
        <p class="st-btn-open" data-st-slidebox-toggle=""><i class="st-fa st-svg-plus-thin" data-st-slidebox-icon="" data-st-slidebox-icon-collapsed="st-svg-plus-thin" data-st-slidebox-icon-expanded="st-svg-minus-thin" aria-hidden=""></i><span class="st-slidebox-btn-text" data-st-slidebox-text="" data-st-slidebox-text-collapsed="クリックして展開" data-st-slidebox-text-expanded="閉じる">クリックして下さい</span></p>
        <div class="st-slidebox" data-st-slidebox-content="">
        <div class="scroll-box">
        売りシグナルテーブル
        {html_table_macd_rsi_sell}
        </div>
        </div>
        </div>
        <p><!-- /wp:st-blocks/st-slidebox --></p>

        <h2>MACD & RCIによる売買シグナル</h2>
        <p>MACDとRCIによるシグナルは下記の条件で導出しています。</p>
        [st-mybox title="買いシグナルの条件" webicon="st-svg-check-circle" color="#03A9F4" bordercolor="#B3E5FC" bgcolor="#E1F5FE" borderwidth="2" borderradius="5" titleweight="bold"]
        <ol>
        <li>MACDがMACDシグナルを上回っている</li>
        <li>RCI短期が50%を上回る</li>
        <li>RCI長期が過去5営業日内に-80%を上回る</li>
        </ol>
        [/st-mybox]
        [st-mybox title="売りシグナルの条件" webicon="st-svg-check-circle" color="#03A9F4" bordercolor="#B3E5FC" bgcolor="#E1F5FE" borderwidth="2" borderradius="5" titleweight="bold"]
        <ol>
        <li>MACDがMACDシグナルを下回っている</li>
        <li>RCI短期が-50%を下回る</li>
        <li>RCI長期が過去5営業日内に80%を下回る</li>
        </ol>
        [/st-mybox]
        <p></p>
        <h3>買いシグナル銘柄（{macd_rci_buy_count}銘柄）</h3>
        <p><!-- wp:st-blocks/st-slidebox --></p>
        <div class="wp-block-st-blocks-st-slidebox st-slidebox-c is-collapsed has-st-toggle-icon is-st-toggle-position-left is-st-toggle-icon-position-left" data-st-slidebox="">
        <p class="st-btn-open" data-st-slidebox-toggle=""><i class="st-fa st-svg-plus-thin" data-st-slidebox-icon="" data-st-slidebox-icon-collapsed="st-svg-plus-thin" data-st-slidebox-icon-expanded="st-svg-minus-thin" aria-hidden=""></i><span class="st-slidebox-btn-text" data-st-slidebox-text="" data-st-slidebox-text-collapsed="クリックして展開" data-st-slidebox-text-expanded="閉じる">クリックして下さい</span></p>
        <div class="st-slidebox" data-st-slidebox-content="">
        <div class="scroll-box">
        買いシグナルテーブル
        {html_table_macd_rci_buy}
        </div>
        </div>
        </div>
        <p><!-- /wp:st-blocks/st-slidebox --></p>
        
        <h3>売りシグナル銘柄（{macd_rci_sell_count}銘柄）</h3>
        <p><!-- wp:st-blocks/st-slidebox --></p>
        <div class="wp-block-st-blocks-st-slidebox st-slidebox-c is-collapsed has-st-toggle-icon is-st-toggle-position-left is-st-toggle-icon-position-left" data-st-slidebox="">
        <p class="st-btn-open" data-st-slidebox-toggle=""><i class="st-fa st-svg-plus-thin" data-st-slidebox-icon="" data-st-slidebox-icon-collapsed="st-svg-plus-thin" data-st-slidebox-icon-expanded="st-svg-minus-thin" aria-hidden=""></i><span class="st-slidebox-btn-text" data-st-slidebox-text="" data-st-slidebox-text-collapsed="クリックして展開" data-st-slidebox-text-expanded="閉じる">クリックして下さい</span></p>
        <div class="st-slidebox" data-st-slidebox-content="">
        <div class="scroll-box">
        売りシグナルテーブル
        {html_table_macd_rci_sell}
        </div>
        </div>
        </div>
        <p><!-- /wp:st-blocks/st-slidebox --></p>

        <h2>MACD & RSI と MACD & RCI による売買シグナル</h2>
        <p>上記のMACDとRSIによる条件とMACDとRCIによる条件の両方を満たしている銘柄です。</p>
        <p></p>
        <h3>買いシグナル銘柄（{macd_rsi_rci_buy_count}銘柄）</h3>
        <p><!-- wp:st-blocks/st-slidebox --></p>
        <div class="wp-block-st-blocks-st-slidebox st-slidebox-c is-collapsed has-st-toggle-icon is-st-toggle-position-left is-st-toggle-icon-position-left" data-st-slidebox="">
        <p class="st-btn-open" data-st-slidebox-toggle=""><i class="st-fa st-svg-plus-thin" data-st-slidebox-icon="" data-st-slidebox-icon-collapsed="st-svg-plus-thin" data-st-slidebox-icon-expanded="st-svg-minus-thin" aria-hidden=""></i><span class="st-slidebox-btn-text" data-st-slidebox-text="" data-st-slidebox-text-collapsed="クリックして展開" data-st-slidebox-text-expanded="閉じる">クリックして下さい</span></p>
        <div class="st-slidebox" data-st-slidebox-content="">
        <div class="scroll-box">
        買いシグナルテーブル
        {html_table_macd_rsi_rci_buy}
        </div>
        </div>
        </div>
        <p><!-- /wp:st-blocks/st-slidebox --></p>
        
        <h3>売りシグナル銘柄（{macd_rsi_rci_sell_count}銘柄）</h3>
        <p><!-- wp:st-blocks/st-slidebox --></p>
        <div class="wp-block-st-blocks-st-slidebox st-slidebox-c is-collapsed has-st-toggle-icon is-st-toggle-position-left is-st-toggle-icon-position-left" data-st-slidebox="">
        <p class="st-btn-open" data-st-slidebox-toggle=""><i class="st-fa st-svg-plus-thin" data-st-slidebox-icon="" data-st-slidebox-icon-collapsed="st-svg-plus-thin" data-st-slidebox-icon-expanded="st-svg-minus-thin" aria-hidden=""></i><span class="st-slidebox-btn-text" data-st-slidebox-text="" data-st-slidebox-text-collapsed="クリックして展開" data-st-slidebox-text-expanded="閉じる">クリックして下さい</span></p>
        <div class="st-slidebox" data-st-slidebox-content="">
        <div class="scroll-box">
        売りシグナルテーブル
        {html_table_macd_rsi_rci_sell}
        </div>
        </div>
        </div>
        <p><!-- /wp:st-blocks/st-slidebox --></p>
        
        <h2>MACD & ボリンジャーバンドによる売買シグナル</h2>
        <p>MACDとボリンジャーバンドによるシグナルは下記の条件で導出しています。</p>
        [st-mybox title="買いシグナルの条件" webicon="st-svg-check-circle" color="#03A9F4" bordercolor="#B3E5FC" bgcolor="#E1F5FE" borderwidth="2" borderradius="5" titleweight="bold"]
        <ol>
        <li>終値が20SMA（BB_Middle）を上回る</li>
        <li>終値が高値と安値の中間よりも上（上髭が短い）</li>
        <li>直近1営業日内にMACDのゴールデンクロス発生</li>
        </ol>
        [/st-mybox]
        [st-mybox title="売りシグナルの条件" webicon="st-svg-check-circle" color="#03A9F4" bordercolor="#B3E5FC" bgcolor="#E1F5FE" borderwidth="2" borderradius="5" titleweight="bold"]
        <ol>
        <li>終値が20SMA（BB_Middle）を下回る</li>
        <li>終値が高値と安値の中間よりも下（下髭が短い）</li>
        <li>直近1営業日内にMACDのデッドクロス発生</li>
        </ol>
        [/st-mybox]
        <p></p>
        <h3>買いシグナル銘柄（{bb_macd_buy_count}銘柄）</h3>
        <p><!-- wp:st-blocks/st-slidebox --></p>
        <div class="wp-block-st-blocks-st-slidebox st-slidebox-c is-collapsed has-st-toggle-icon is-st-toggle-position-left is-st-toggle-icon-position-left" data-st-slidebox="">
        <p class="st-btn-open" data-st-slidebox-toggle=""><i class="st-fa st-svg-plus-thin" data-st-slidebox-icon="" data-st-slidebox-icon-collapsed="st-svg-plus-thin" data-st-slidebox-icon-expanded="st-svg-minus-thin" aria-hidden=""></i><span class="st-slidebox-btn-text" data-st-slidebox-text="" data-st-slidebox-text-collapsed="クリックして展開" data-st-slidebox-text-expanded="閉じる">クリックして下さい</span></p>
        <div class="st-slidebox" data-st-slidebox-content="">
        <div class="scroll-box">
        買いシグナルテーブル
        {html_table_bb_macd_buy}
        </div>
        </div>
        </div>
        <p><!-- /wp:st-blocks/st-slidebox --></p>
        
        <h3>売りシグナル銘柄（{bb_macd_sell_count}銘柄）</h3>
        <p><!-- wp:st-blocks/st-slidebox --></p>
        <div class="wp-block-st-blocks-st-slidebox st-slidebox-c is-collapsed has-st-toggle-icon is-st-toggle-position-left is-st-toggle-icon-position-left" data-st-slidebox="">
        <p class="st-btn-open" data-st-slidebox-toggle=""><i class="st-fa st-svg-plus-thin" data-st-slidebox-icon="" data-st-slidebox-icon-collapsed="st-svg-plus-thin" data-st-slidebox-icon-expanded="st-svg-minus-thin" aria-hidden=""></i><span class="st-slidebox-btn-text" data-st-slidebox-text="" data-st-slidebox-text-collapsed="クリックして展開" data-st-slidebox-text-expanded="閉じる">クリックして下さい</span></p>
        <div class="st-slidebox" data-st-slidebox-content="">
        <div class="scroll-box">
        売りシグナルテーブル
        {html_table_bb_macd_sell}
        </div>
        </div>
        </div>
        <p><!-- /wp:st-blocks/st-slidebox --></p>
        
        <h2>強いトレンド銘柄</h2>
        <p>目先のトレンドが強い銘柄を下記の条件で抽出しています。</p>
        [st-mybox title="強い買いトレンド抽出の条件" webicon="st-svg-check-circle" color="#03A9F4" bordercolor="#B3E5FC" bgcolor="#E1F5FE" borderwidth="2" borderradius="5" titleweight="bold"]
        <ol>
        <li>前の営業日の短期移動平均と中期移動平均の差分よりも、最新の短期移動平均と中期移動平均の差分の方が大きい</li>
        <li>「短期移動平均 ＞ 中期移動平均 ＞ 長期移動平均」の関係が成立している</li>
        <li>最新の終値が短期移動平均よりも高い</li>
        <li>出来高が100,000以上</li>
        </ol>
        [/st-mybox]
        [st-mybox title="強い売りトレンド抽出の条件" webicon="st-svg-check-circle" color="#03A9F4" bordercolor="#B3E5FC" bgcolor="#E1F5FE" borderwidth="2" borderradius="5" titleweight="bold"]
        <ol>
        <li>前の営業日の中期移動平均と短期移動平均の差分よりも、最新の中期移動平均と短期移動平均の差分の方が大きい</li>
        <li>「短期移動平均 ＜ 中期移動平均 ＜ 長期移動平均」の関係が成立している</li>
        <li>最新の終値が短期移動平均よりも安い</li>
        <li>出来高が100,000以上</li>
        </ol>
        [/st-mybox]
        <h3>強い買いトレンド銘柄（{strong_buying_count}銘柄）</h3>
        <p><!-- wp:st-blocks/st-slidebox --></p>
        <div class="wp-block-st-blocks-st-slidebox st-slidebox-c is-collapsed has-st-toggle-icon is-st-toggle-position-left is-st-toggle-icon-position-left" data-st-slidebox="">
        <p class="st-btn-open" data-st-slidebox-toggle=""><i class="st-fa st-svg-plus-thin" data-st-slidebox-icon="" data-st-slidebox-icon-collapsed="st-svg-plus-thin" data-st-slidebox-icon-expanded="st-svg-minus-thin" aria-hidden=""></i><span class="st-slidebox-btn-text" data-st-slidebox-text="" data-st-slidebox-text-collapsed="クリックして展開" data-st-slidebox-text-expanded="閉じる">クリックして下さい</span></p>
        <div class="st-slidebox" data-st-slidebox-content="">
        <div class="scroll-box">
        強い買いトレンド銘柄テーブル
        {html_table_strong_buying}
        </div>
        </div>
        </div>
        <p><!-- /wp:st-blocks/st-slidebox --></p>
        
        <h3>強い売りトレンド銘柄（{strong_selling_count}銘柄）</h3>
        <p><!-- wp:st-blocks/st-slidebox --></p>
        <div class="wp-block-st-blocks-st-slidebox st-slidebox-c is-collapsed has-st-toggle-icon is-st-toggle-position-left is-st-toggle-icon-position-left" data-st-slidebox="">
        <p class="st-btn-open" data-st-slidebox-toggle=""><i class="st-fa st-svg-plus-thin" data-st-slidebox-icon="" data-st-slidebox-icon-collapsed="st-svg-plus-thin" data-st-slidebox-icon-expanded="st-svg-minus-thin" aria-hidden=""></i><span class="st-slidebox-btn-text" data-st-slidebox-text="" data-st-slidebox-text-collapsed="クリックして展開" data-st-slidebox-text-expanded="閉じる">クリックして下さい</span></p>
        <div class="st-slidebox" data-st-slidebox-content="">
        <div class="scroll-box">
        強い売りトレンド銘柄テーブル
        {html_table_strong_selling}
        </div>
        </div>
        </div>
        <p><!-- /wp:st-blocks/st-slidebox --></p>

        <h2>押し目狙い銘柄 ({push_mark_count})</h2>
        <p>短期移動平均が中期移動平均に近付いた、押し目狙いの銘柄です。</p>
        <p>下記の条件で抽出しています。
        </p>[st-mybox title="押し目狙い銘柄を抽出する条件" webicon="st-svg-check-circle" color="#03A9F4" bordercolor="#B3E5FC" bgcolor="#E1F5FE" borderwidth="2" borderradius="5" titleweight="bold"]
        <ol>
        <li>「短期移動平均-中期移動平均」の絶対値がその銘柄の最新Close値の2%以下</li>
        <li>短期移動平均と中期移動平均の差が+方向に広がった</li>
        <li>中期移動平均線が上向いている(前営業日からの変化率が0.3%以上)</li>
        <li>最新の出来高が10万以上</li>
        </ol>
        [/st-mybox]        
        <p><!-- wp:st-blocks/st-slidebox --></p>
        <div class="wp-block-st-blocks-st-slidebox st-slidebox-c is-collapsed has-st-toggle-icon is-st-toggle-position-left is-st-toggle-icon-position-left" data-st-slidebox="">
        <p class="st-btn-open" data-st-slidebox-toggle=""><i class="st-fa st-svg-plus-thin" data-st-slidebox-icon="" data-st-slidebox-icon-collapsed="st-svg-plus-thin" data-st-slidebox-icon-expanded="st-svg-minus-thin" aria-hidden=""></i><span class="st-slidebox-btn-text" data-st-slidebox-text="" data-st-slidebox-text-collapsed="クリックして展開" data-st-slidebox-text-expanded="閉じる">クリックして下さい</span></p>
        <div class="st-slidebox" data-st-slidebox-content="">
        <div class="scroll-box">
        押し目狙い銘柄
        {html_table_push_mark}
        </div>
        </div>
        </div>
        <p><!-- /wp:st-blocks/st-slidebox --></p>

        <h2>ブレイク銘柄 ({breakout_count})</h2>
        <p>過去3か月間の最高値を更新した銘柄です。</p>
        <p>下記の条件で抽出しています。
        </p>[st-mybox title="ブレイク銘柄を抽出する条件" webicon="st-svg-check-circle" color="#03A9F4" bordercolor="#B3E5FC" bgcolor="#E1F5FE" borderwidth="2" borderradius="5" titleweight="bold"]
        <ol>
        <li>最新の終値が過去3か月間の最高値を上回っている</li>
        <li>最新の出来高が過去3か月間の出来高平均値の1.5倍よりも多い</li>
        <li>終値が高値と安値の中間値よりも高い</li>
        <li>最新の出来高が10万以上</li>
        </ol>
        [/st-mybox]        
        <p><!-- wp:st-blocks/st-slidebox --></p>
        <div class="wp-block-st-blocks-st-slidebox st-slidebox-c is-collapsed has-st-toggle-icon is-st-toggle-position-left is-st-toggle-icon-position-left" data-st-slidebox="">
        <p class="st-btn-open" data-st-slidebox-toggle=""><i class="st-fa st-svg-plus-thin" data-st-slidebox-icon="" data-st-slidebox-icon-collapsed="st-svg-plus-thin" data-st-slidebox-icon-expanded="st-svg-minus-thin" aria-hidden=""></i><span class="st-slidebox-btn-text" data-st-slidebox-text="" data-st-slidebox-text-collapsed="クリックして展開" data-st-slidebox-text-expanded="閉じる">クリックして下さい</span></p>
        <div class="st-slidebox" data-st-slidebox-content="">
        <div class="scroll-box">
        ブレイク銘柄
        {html_table_breakout}
        </div>
        </div>
        </div>
        <p><!-- /wp:st-blocks/st-slidebox --></p>
        """
    
    # ブレイク銘柄のチャートを生成
    print("ブレイク銘柄のチャートを生成中...")
    company_names = load_company_names()
    chart_img_paths = []
    
    # ブレイク銘柄ファイルから銘柄を読み込み
    try:
        # ブレイク銘柄ファイルのパスを動的に決定
        breakout_file_path = breakout_csv_file_path
        if not os.path.exists(breakout_file_path):
            range_brake_path = breakout_csv_file_path.replace("Breakout.csv", "Range_Brake.csv")
            if os.path.exists(range_brake_path):
                breakout_file_path = range_brake_path
                print(f"Breakout.csvが見つからないため、Range_Brake.csvを使用します: {range_brake_path}")
        
        breakout_df = pd.read_csv(breakout_file_path, encoding='utf-8-sig')
        breakout_tickers = breakout_df['Ticker'].tolist()
        
        # 各銘柄のチャートを生成（全件）
        for i, ticker in enumerate(breakout_tickers):
            try:
                chart_path = generate_chart(ticker, company_names)
                if chart_path:
                    chart_img_paths.append(chart_path)
                    print(f"✓ {ticker} のチャートを生成")
                else:
                    print(f"✗ {ticker} のチャート生成に失敗")
            except Exception as e:
                print(f"✗ {ticker} のチャート生成でエラー: {str(e)}")
        
        # チャートを結合（10銘柄ずつに分割）
        combined_chart_paths = combine_charts(chart_img_paths, charts_per_image=10)
        
        if combined_chart_paths:
            charts_images_html = ""
            for i, chart_path in enumerate(combined_chart_paths):
                url = upload_image_to_wordpress(chart_path)
                if url:
                    charts_images_html += f"<div style=\"margin: 20px 0; text-align: center;\"><img src=\"{url}\" alt=\"レンジブレイク銘柄チャート\" style=\"max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px;\"></div>"
                    print(f"✓ チャート {i+1} を投稿内容に追加")
                else:
                    print(f"✗ チャート {i+1} の画像アップロードに失敗: {chart_path}")
            
            if charts_images_html:
                charts_section = f"""
                <h2>ブレイク銘柄チャート</h2>
                <p>各銘柄の株価チャートです。過去6ヶ月間の価格推移と出来高を表示しています。</p>
                <p><!-- wp:st-blocks/st-slidebox --></p>
                <div class="wp-block-st-blocks-st-slidebox st-slidebox-c is-collapsed has-st-toggle-icon is-st-toggle-position-left is-st-toggle-icon-position-left" data-st-slidebox="">
                <p class="st-btn-open" data-st-slidebox-toggle=""><i class="st-fa st-svg-plus-thin" data-st-slidebox-icon="" data-st-slidebox-icon-collapsed="st-svg-plus-thin" data-st-slidebox-icon-expanded="st-svg-minus-thin" aria-hidden=""></i><span class="st-slidebox-btn-text" data-st-slidebox-text="" data-st-slidebox-text-collapsed="クリックして展開" data-st-slidebox-text-expanded="閉じる">クリックして下さい</span></p>
                <div class="st-slidebox" data-st-slidebox-content="">
                <div class="scroll-box">
                {charts_images_html}
                </div>
                </div>
                </div>
                <p><!-- /wp:st-blocks/st-slidebox --></p>
                """
                post_content += charts_section
                print(f"✓ 全チャートを投稿内容に追加")
        else:
            print("⚠ 投稿するチャートがありません")
            
    except Exception as e:
        print(f"ブレイク銘柄のチャート生成でエラー: {e}")
    
    # WordPressに投稿を送信
    post_to_wordpress(post_title, post_content)
    # print(post_content)  # デバッグ用：投稿内容をコンソールに出力（必要に応じてコメント解除）


# スクリプトが直接実行された場合の処理
if __name__ == "__main__":
    main()  # メイン処理を実行