"""
株価分析結果をWordPressに自動投稿するスクリプト

このスクリプトは、株価シグナル分析の結果をWordPressサイトに自動投稿します。
主な機能：
1. 投稿する各種CSVファイルを読み込み
2. CSVデータをHTML形式のテーブルに変換
3. WordPress REST APIを使用して記事を投稿
4. 記事内に展開可能なブロックとして表を表示
"""
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta

# WordPressサイトの接続情報を設定
WP_SITE_URL = "https://www.takstorage.site/"  # WordPressサイトのURL
WP_API_ENDPOINT = f"{WP_SITE_URL}/wp-json/wp/v2/posts"  # WordPress REST API 投稿用エンドポイント
WP_USERNAME = "tak.note7120@gmail.com"  # WordPressの管理者ユーザー名（メールアドレス）
WP_APP_PASSWORD = "GNrk aQ3d 7GWu p1fw dCfM pAGH"  # WordPress アプリケーションパスワード（セキュリティ向上のため通常のパスワードではなくアプリパスワードを使用）

# 今日の日付と昨日の日付を取得（昨日の株価データを投稿するため）
current_date = (datetime.now()).strftime("%Y/%m/%d")  # YYYY/MM/DD形式

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
    
    Args:
        csv_file_path (str): 読み込むCSVファイルのパス
        
    Returns:
        tuple: (スタイル適用済みのHTML表（スクロール可能なコンテナ内）, 銘柄数)
    """
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

def main():
    """
    メイン処理：CSVファイルの読み込み、HTML変換、WordPress投稿を実行
    """
    # 読み込むCSVファイルのパス
    # ここを変更：StockSignal → StockAnalysis_Technical
    macd_rsi_signal_buy_csv_file_path = "C:\\Users\\mount\\Git\\StockAnalysis_Technical\\StockSignal\\Result\\macd_rsi_signal_result_buy.csv"   # 買いシグナルCSV
    macd_rsi_signal_sell_csv_file_path = "C:\\Users\\mount\\Git\\StockAnalysis_Technical\\StockSignal\\Result\\macd_rsi_signal_result_sell.csv" # 売りシグナルCSV
    macd_rci_signal_buy_csv_file_path = "C:\\Users\\mount\\Git\\StockAnalysis_Technical\\StockSignal\\Result\\macd_rci_signal_result_buy.csv"   # 買いシグナルCSV
    macd_rci_signal_sell_csv_file_path = "C:\\Users\\mount\\Git\\StockAnalysis_Technical\\StockSignal\\Result\\macd_rci_signal_result_sell.csv" # 売りシグナルCSV
    macd_rsi_rci_signal_buy_csv_file_path = "C:\\Users\\mount\\Git\\StockAnalysis_Technical\\StockSignal\\Result\\macd_rsi_rci_signal_result_buy.csv"   # 買いシグナルCSV
    macd_rsi_rci_signal_sell_csv_file_path = "C:\\Users\\mount\\Git\\StockAnalysis_Technical\\StockSignal\\Result\\macd_rsi_rci_signal_result_sell.csv" # 売りシグナルCSV
    range_break_csv_file_path = "C:\\Users\\mount\\Git\\StockAnalysis_Technical\\StockSignal\\Result\\Range_Brake.csv" # レンジブレイク銘柄CSV
    strong_buying_csv_file_path = "C:\\Users\\mount\\Git\\StockAnalysis_Technical\\StockSignal\\Result\\strong_buying_trend.csv" # 強い買いトレンド銘柄抽出
    strong_selling_csv_file_path = "C:\\Users\\mount\\Git\\StockAnalysis_Technical\\StockSignal\\Result\\strong_selling_trend.csv" # 強い売りトレンド銘柄抽出
    
    # 各CSVファイルを読み込んで、銘柄コード(Ticker)列で昇順ソートして再保存
    # 表示時に銘柄コードでソートされた状態にするため
    for file_path in [macd_rsi_signal_buy_csv_file_path, macd_rsi_signal_sell_csv_file_path, macd_rci_signal_buy_csv_file_path, macd_rci_signal_sell_csv_file_path, macd_rsi_rci_signal_buy_csv_file_path, macd_rsi_rci_signal_sell_csv_file_path, macd_rsi_rci_signal_sell_csv_file_path]:
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
    html_table_range_break, range_break_count = read_csv_to_html_table(range_break_csv_file_path) # レンジブレイク銘柄テーブル
    html_table_strong_buying, strong_buying_count = read_csv_to_html_table(strong_buying_csv_file_path) # 強い買いトレンド銘柄テーブル
    html_table_strong_selling, strong_selling_count = read_csv_to_html_table(strong_selling_csv_file_path) # 強い売りトレンド銘柄テーブル
    
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
        
        <h2>強いトレンド銘柄</h2>
        <p>目先のトレンドが強い銘柄を下記の条件で抽出しています。</p>
        [st-mybox title="強い買いトレンド抽出の条件" webicon="st-svg-check-circle" color="#03A9F4" bordercolor="#B3E5FC" bgcolor="#E1F5FE" borderwidth="2" borderradius="5" titleweight="bold"]
        <ol>
        <li>前の営業日の短期移動平均と中期移動平均の差分よりも、最新の短期移動平均と中期移動平均の差分の方が大きい</li>
        <li>「短期移動平均 ＞ 中期移動平均 ＞ 長期移動平均」の関係が成立している</li>
        <li>最新の終値が短期移動平均よりも高い</li>
        </ol>
        [/st-mybox]
        [st-mybox title="強い売りトレンド抽出の条件" webicon="st-svg-check-circle" color="#03A9F4" bordercolor="#B3E5FC" bgcolor="#E1F5FE" borderwidth="2" borderradius="5" titleweight="bold"]
        <ol>
        <li>前の営業日の中期移動平均と短期移動平均の差分よりも、最新の中期移動平均と短期移動平均の差分の方が大きい</li>
        <li>「短期移動平均 ＜ 中期移動平均 ＜ 長期移動平均」の関係が成立している</li>
        <li>最新の終値が短期移動平均よりも安い</li>
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

        <h2>レンジブレイク銘柄 ({range_break_count})</h2>
        <p>過去1か月間の最高値を更新した銘柄です。</p>
        <p>下記の条件で抽出しています。
        </p>[st-mybox title="レンジブレイク銘柄を抽出する条件" webicon="st-svg-check-circle" color="#03A9F4" bordercolor="#B3E5FC" bgcolor="#E1F5FE" borderwidth="2" borderradius="5" titleweight="bold"]
        <ol>
        <li>最新の終値が過去1か月間の最高値を上回っている</li>
        <li>最新の出来高が過去1か月間の出来高平均値の1.5倍よりも多い</li>
        <li>最高値と終値の差分が0.5%以下</li>
        <li>最新の出来高が10万以上</li>
        </ol>
        [/st-mybox]        
        <p><!-- wp:st-blocks/st-slidebox --></p>
        <div class="wp-block-st-blocks-st-slidebox st-slidebox-c is-collapsed has-st-toggle-icon is-st-toggle-position-left is-st-toggle-icon-position-left" data-st-slidebox="">
        <p class="st-btn-open" data-st-slidebox-toggle=""><i class="st-fa st-svg-plus-thin" data-st-slidebox-icon="" data-st-slidebox-icon-collapsed="st-svg-plus-thin" data-st-slidebox-icon-expanded="st-svg-minus-thin" aria-hidden=""></i><span class="st-slidebox-btn-text" data-st-slidebox-text="" data-st-slidebox-text-collapsed="クリックして展開" data-st-slidebox-text-expanded="閉じる">クリックして下さい</span></p>
        <div class="st-slidebox" data-st-slidebox-content="">
        <div class="scroll-box">
        レンジブレイク銘柄
        {html_table_range_break}
        </div>
        </div>
        </div>
        <p><!-- /wp:st-blocks/st-slidebox --></p>
        """
    
    # WordPressに投稿を送信
    post_to_wordpress(post_title, post_content)
    # print(post_content)  # デバッグ用：投稿内容をコンソールに出力（必要に応じてコメント解除）


# スクリプトが直接実行された場合の処理
if __name__ == "__main__":
    main()  # メイン処理を実行