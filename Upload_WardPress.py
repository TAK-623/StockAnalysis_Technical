import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta

# WordPressサイトの情報を設定
WP_SITE_URL = "https://www.takstorage.site/"  # WordPressサイトのURL
WP_API_ENDPOINT = f"{WP_SITE_URL}/wp-json/wp/v2/posts"  # 投稿用のエンドポイント
WP_USERNAME = "tak.note7120@gmail.com"  # WordPressのユーザー名
WP_APP_PASSWORD = "GNrk aQ3d 7GWu p1fw dCfM pAGH"  # アプリケーションパスワード
current_date = datetime.now()
yesterday_date = (current_date - timedelta(days=1)).strftime("%Y/%m/%d")  # 必要に応じてフォーマット変更

# 投稿の冒頭部分のテキスト
intro_text = """
<p>{yesterday_date}終わり時点での情報です。</p>
<p>Pythonを使用して自動でデータ収集&演算を行い、自動で投稿しています。</p>
<p>銘柄名冒頭のアルファベットの意味は下記です。</p>
<div class="graybox">
<p>P: プライム市場の銘柄</p>
<p>S: スタンダード市場の銘柄</p>
<p>G: グロース市場の銘柄</p>
</div>
<p>※三役好転・三役暗転の判定は2025/1/19以降の実施のため、それ以前に三役好転・三役暗転状態になっている銘柄は抽出できていません。</p>
""".format(yesterday_date=yesterday_date)

# CSVファイルを読み込む関数
def read_csv_to_html_table(csv_file_path, decimal_places=2):
    df = pd.read_csv(csv_file_path)

    # 小数点以下の桁数を統一（float型の列のみ適用）
    for col in df.select_dtypes(include=['float']):
        df[col] = df[col].round(decimal_places)

    # DataFrame を HTML に変換
    df_html = df.to_html(index=False, border=1, escape=False)

    # Name列（1列目）の最大幅を制限
    df_html = df_html.replace('<th>', '<th style="max-width:800px; white-space:nowrap; overflow:hidden;">')
    df_html = df_html.replace('<td>', '<td style="max-width:800px; word-wrap:break-word;">')

    # スクロール可能な div でラップ
    styled_table = f"""
    <div class="scroll-box">
        {df_html}
    </div>
    """
    return styled_table

# WordPressに投稿を送信する関数
def post_to_wordpress(title, post_content):
    # 投稿のデータ
    post_data = {
        "title": title,
        "content": post_content,
        "status": "publish",  # 投稿を公開する
        "categories": [20],
        "tags": [19],
        "featured_media": 233
    }
    # リクエストを送信
    response = requests.post(
        WP_API_ENDPOINT,
        json=post_data,
        auth=HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD)
    )
    # レスポンスを確認
    if response.status_code == 201:  # 投稿成功
        print("投稿が成功しました:", response.json()["link"])
    else:
        print("投稿に失敗しました:", response.status_code, response.text)

# メイン処理
def main():
    # CSVファイルのパス
    kouten_csv_file_path = "C:\\Users\\mount\\Git\\MyProject\\stockSignal\\ichimoku_for_blog_kouten.csv"
    anten_csv_file_path = "C:\\Users\\mount\\Git\\MyProject\\stockSignal\\ichimoku_for_blog_anten.csv"
    kouten_start_csv_file_path = "C:\\Users\\mount\\Git\\MyProject\\stockSignal\\ichimoku_for_blog_kouten_start.csv"
    anten_start_csv_file_path = "C:\\Users\\mount\\Git\\MyProject\\stockSignal\\ichimoku_for_blog_anten_start.csv"
    kouten_end_csv_file_path = "C:\\Users\\mount\\Git\\MyProject\\stockSignal\\ichimoku_for_blog_kouten_end.csv"
    anten_end_csv_file_path = "C:\\Users\\mount\\Git\\MyProject\\stockSignal\\ichimoku_for_blog_anten_end.csv"
    
    # 各CSVファイルを読み込んで Ticker 列で昇順ソートし、再度保存
    for file_path in [kouten_csv_file_path, anten_csv_file_path, kouten_start_csv_file_path, anten_start_csv_file_path, kouten_end_csv_file_path, anten_end_csv_file_path]:
        df = pd.read_csv(file_path, encoding='utf-8')  # CSVファイルを読み込む
        df_sorted = df.sort_values(by='Ticker')  # Ticker 列を昇順ソート
        df_sorted.to_csv(file_path, index=False, encoding='utf-8')  # ソート後に保存
    
    # CSVをHTML表に変換
    html_table_kouten = read_csv_to_html_table(kouten_csv_file_path)
    html_table_anten = read_csv_to_html_table(anten_csv_file_path)
    html_table_kouten_start = read_csv_to_html_table(kouten_start_csv_file_path)
    html_table_anten_start = read_csv_to_html_table(anten_start_csv_file_path)
    html_table_kouten_end = read_csv_to_html_table(kouten_end_csv_file_path)
    html_table_anten_end = read_csv_to_html_table(anten_end_csv_file_path)
    
    # 投稿のタイトルと内容
    post_title = "一目均衡表情報_{yesterday_date}".format(yesterday_date=yesterday_date)  # 投稿タイトル
    
    post_content = f"""
        {intro_text}
        <h2>一目均衡表</h2>
        <p>三役好転・三役暗転の情報を抽出しました</p>
        <h3>三役好転銘柄</h3>
        <p><!-- wp:st-blocks/st-slidebox --></p>
        <div class="wp-block-st-blocks-st-slidebox st-slidebox-c is-collapsed has-st-toggle-icon is-st-toggle-position-left is-st-toggle-icon-position-left" data-st-slidebox="">
        <p class="st-btn-open" data-st-slidebox-toggle=""><i class="st-fa st-svg-plus-thin" data-st-slidebox-icon="" data-st-slidebox-icon-collapsed="st-svg-plus-thin" data-st-slidebox-icon-expanded="st-svg-minus-thin" aria-hidden=""></i><span class="st-slidebox-btn-text" data-st-slidebox-text="" data-st-slidebox-text-collapsed="クリックして展開" data-st-slidebox-text-expanded="閉じる">クリックして下さい</span></p>
        <div class="st-slidebox" data-st-slidebox-content="">
        <div class="scroll-box">
        三役好転テーブル
        {html_table_kouten}
        </div>
        </div>
        </div>
        <p><!-- /wp:st-blocks/st-slidebox --></p>
        
        <h3>三役暗転銘柄</h3>
        <p><!-- wp:st-blocks/st-slidebox --></p>
        <div class="wp-block-st-blocks-st-slidebox st-slidebox-c is-collapsed has-st-toggle-icon is-st-toggle-position-left is-st-toggle-icon-position-left" data-st-slidebox="">
        <p class="st-btn-open" data-st-slidebox-toggle=""><i class="st-fa st-svg-plus-thin" data-st-slidebox-icon="" data-st-slidebox-icon-collapsed="st-svg-plus-thin" data-st-slidebox-icon-expanded="st-svg-minus-thin" aria-hidden=""></i><span class="st-slidebox-btn-text" data-st-slidebox-text="" data-st-slidebox-text-collapsed="クリックして展開" data-st-slidebox-text-expanded="閉じる">クリックして下さい</span></p>
        <div class="st-slidebox" data-st-slidebox-content="">
        <div class="scroll-box">
        三役暗転テーブル
        {html_table_anten}
        </div>
        </div>
        </div>
        <p><!-- /wp:st-blocks/st-slidebox --></p>
        
        <h3>三役好転した銘柄</h3>
        <p><!-- wp:st-blocks/st-slidebox --></p>
        <div class="wp-block-st-blocks-st-slidebox st-slidebox-c is-collapsed has-st-toggle-icon is-st-toggle-position-left is-st-toggle-icon-position-left" data-st-slidebox="">
        <p class="st-btn-open" data-st-slidebox-toggle=""><i class="st-fa st-svg-plus-thin" data-st-slidebox-icon="" data-st-slidebox-icon-collapsed="st-svg-plus-thin" data-st-slidebox-icon-expanded="st-svg-minus-thin" aria-hidden=""></i><span class="st-slidebox-btn-text" data-st-slidebox-text="" data-st-slidebox-text-collapsed="クリックして展開" data-st-slidebox-text-expanded="閉じる">クリックして下さい</span></p>
        <div class="st-slidebox" data-st-slidebox-content="">
        <div class="scroll-box">
        三役好転開始テーブル
        {html_table_kouten_start}
        </div>
        </div>
        </div>
        <p><!-- /wp:st-blocks/st-slidebox --></p>
        
        <h3>三役暗転した銘柄</h3>
        <p><!-- wp:st-blocks/st-slidebox --></p>
        <div class="wp-block-st-blocks-st-slidebox st-slidebox-c is-collapsed has-st-toggle-icon is-st-toggle-position-left is-st-toggle-icon-position-left" data-st-slidebox="">
        <p class="st-btn-open" data-st-slidebox-toggle=""><i class="st-fa st-svg-plus-thin" data-st-slidebox-icon="" data-st-slidebox-icon-collapsed="st-svg-plus-thin" data-st-slidebox-icon-expanded="st-svg-minus-thin" aria-hidden=""></i><span class="st-slidebox-btn-text" data-st-slidebox-text="" data-st-slidebox-text-collapsed="クリックして展開" data-st-slidebox-text-expanded="閉じる">クリックして下さい</span></p>
        <div class="st-slidebox" data-st-slidebox-content="">
        <div class="scroll-box">
        三役暗転開始テーブル
        {html_table_anten_start}
        </div>
        </div>
        </div>
        <p><!-- /wp:st-blocks/st-slidebox --></p>
        
        <h3>三役好転が終了した銘柄</h3>
        <p><!-- wp:st-blocks/st-slidebox --></p>
        <div class="wp-block-st-blocks-st-slidebox st-slidebox-c is-collapsed has-st-toggle-icon is-st-toggle-position-left is-st-toggle-icon-position-left" data-st-slidebox="">
        <p class="st-btn-open" data-st-slidebox-toggle=""><i class="st-fa st-svg-plus-thin" data-st-slidebox-icon="" data-st-slidebox-icon-collapsed="st-svg-plus-thin" data-st-slidebox-icon-expanded="st-svg-minus-thin" aria-hidden=""></i><span class="st-slidebox-btn-text" data-st-slidebox-text="" data-st-slidebox-text-collapsed="クリックして展開" data-st-slidebox-text-expanded="閉じる">クリックして下さい</span></p>
        <div class="st-slidebox" data-st-slidebox-content="">
        <div class="scroll-box">
        三役好転終了テーブル
        {html_table_kouten_end}
        </div>
        </div>
        </div>
        <p><!-- /wp:st-blocks/st-slidebox --></p>
        
        <h3>三役暗転が終了した銘柄</h3>
        <p><!-- wp:st-blocks/st-slidebox --></p>
        <div class="wp-block-st-blocks-st-slidebox st-slidebox-c is-collapsed has-st-toggle-icon is-st-toggle-position-left is-st-toggle-icon-position-left" data-st-slidebox="">
        <p class="st-btn-open" data-st-slidebox-toggle=""><i class="st-fa st-svg-plus-thin" data-st-slidebox-icon="" data-st-slidebox-icon-collapsed="st-svg-plus-thin" data-st-slidebox-icon-expanded="st-svg-minus-thin" aria-hidden=""></i><span class="st-slidebox-btn-text" data-st-slidebox-text="" data-st-slidebox-text-collapsed="クリックして展開" data-st-slidebox-text-expanded="閉じる">クリックして下さい</span></p>
        <div class="st-slidebox" data-st-slidebox-content="">
        <div class="scroll-box">
        三役暗転終了テーブル
        {html_table_anten_end}
        </div>
        </div>
        </div>
        <p><!-- /wp:st-blocks/st-slidebox --></p>
        """
    
    # WordPressに投稿
    post_to_wordpress(post_title, post_content)
    # print(post_content)  # 投稿内容を出力して確認


if __name__ == "__main__":
    main()
