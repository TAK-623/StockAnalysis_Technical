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
        "categories": [22],
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
    signal_buy_csv_file_path = "C:\\Users\\mount\\Git\\StockSignal\\Result\\signal_result_buy.csv"
    signal_sell_csv_file_path = "C:\\Users\\mount\\Git\\StockSignal\\Result\\signal_result_sell.csv"
    
    # 各CSVファイルを読み込んで Ticker 列で昇順ソートし、再度保存
    for file_path in [signal_buy_csv_file_path, signal_sell_csv_file_path]:
        df = pd.read_csv(file_path, encoding='utf-8')  # CSVファイルを読み込む
        df_sorted = df.sort_values(by='Ticker')  # Ticker 列を昇順ソート
        df_sorted.to_csv(file_path, index=False, encoding='utf-8')  # ソート後に保存
    
    # CSVをHTML表に変換
    html_table_buy = read_csv_to_html_table(signal_buy_csv_file_path)
    html_table_sell = read_csv_to_html_table(signal_sell_csv_file_path)
    
    # 投稿のタイトルと内容
    post_title = "売り買いシグナル_{yesterday_date}".format(yesterday_date=yesterday_date)  # 投稿タイトル
    
    post_content = f"""
        {intro_text}
        <h2>売り買いシグナル</h2>
        <p>独自の条件でフィルタリングした銘柄を抽出しています。</p>
        <h3>買いシグナル銘柄</h3>
        <p><!-- wp:st-blocks/st-slidebox --></p>
        <div class="wp-block-st-blocks-st-slidebox st-slidebox-c is-collapsed has-st-toggle-icon is-st-toggle-position-left is-st-toggle-icon-position-left" data-st-slidebox="">
        <p class="st-btn-open" data-st-slidebox-toggle=""><i class="st-fa st-svg-plus-thin" data-st-slidebox-icon="" data-st-slidebox-icon-collapsed="st-svg-plus-thin" data-st-slidebox-icon-expanded="st-svg-minus-thin" aria-hidden=""></i><span class="st-slidebox-btn-text" data-st-slidebox-text="" data-st-slidebox-text-collapsed="クリックして展開" data-st-slidebox-text-expanded="閉じる">クリックして下さい</span></p>
        <div class="st-slidebox" data-st-slidebox-content="">
        <div class="scroll-box">
        買いシグナルテーブル
        {html_table_buy}
        </div>
        </div>
        </div>
        <p><!-- /wp:st-blocks/st-slidebox --></p>
        
        <h3>売りシグナル銘柄</h3>
        <p><!-- wp:st-blocks/st-slidebox --></p>
        <div class="wp-block-st-blocks-st-slidebox st-slidebox-c is-collapsed has-st-toggle-icon is-st-toggle-position-left is-st-toggle-icon-position-left" data-st-slidebox="">
        <p class="st-btn-open" data-st-slidebox-toggle=""><i class="st-fa st-svg-plus-thin" data-st-slidebox-icon="" data-st-slidebox-icon-collapsed="st-svg-plus-thin" data-st-slidebox-icon-expanded="st-svg-minus-thin" aria-hidden=""></i><span class="st-slidebox-btn-text" data-st-slidebox-text="" data-st-slidebox-text-collapsed="クリックして展開" data-st-slidebox-text-expanded="閉じる">クリックして下さい</span></p>
        <div class="st-slidebox" data-st-slidebox-content="">
        <div class="scroll-box">
        売りシグナルテーブル
        {html_table_sell}
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
