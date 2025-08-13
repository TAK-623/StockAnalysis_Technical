"""
一目均衡表WordPress投稿モジュール - 一目均衡表分析結果の自動投稿

このスクリプトは、株価シグナル分析の一目均衡表に関する結果をWordPressサイトに自動投稿します。
主な機能：
1. 一目均衡表関連のCSVファイルを読み込み
2. CSVデータをHTML形式のテーブルに変換
3. WordPress REST APIを使用して記事を投稿
4. 記事内に展開可能なブロックとして表を表示

投稿内容：
- 一目均衡表 雲の下でゴールデンクロス銘柄
- 一目均衡表 雲の上でゴールデンクロス銘柄
- 一目均衡表 雲の下でデッドクロス銘柄
- 一目均衡表 雲の上でデッドクロス銘柄
- 一目均衡表 三役好転銘柄
- 一目均衡表 三役暗転銘柄

一目均衡表の特徴：
- 日本で開発された複合テクニカル指標
- 転換線、基準線、先行スパンA/B、遅行スパンで構成
- 雲（Kumo）によるサポート・レジスタンス表示
- トレンド転換のタイミングを予測

使用技術：
- WordPress REST API
- pandas（データ処理）
- HTML/CSS（テーブルスタイリング）
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
<p>Pythonを使用して自動でデータ収集&演算を行い、一目均衡表の情報を抽出しています。</p>
<p>銘柄名に付いているアルファベットで市場を表しています。</p>
<div class="graybox">
<p>P: プライム市場の銘柄</p>
<p>S: スタンダード市場の銘柄</p>
<p>G: グロース市場の銘柄</p>
</div>
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
        "categories": [20],         # カテゴリーID（22=株価情報カテゴリー）
        "tags": [19],               # タグID（19=株価情報タグ）
        "featured_media": 1003      # アイキャッチ画像ID
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
    sanyaku_kouten_csv_file_path = "C:\\Users\\mount\\Git\\StockAnalysis_Technical\\StockSignal\\Result\\sanyaku_kouten.csv"   # 三役好転銘柄
    sanyaku_anten_csv_file_path = "C:\\Users\\mount\\Git\\StockAnalysis_Technical\\StockSignal\\Result\\sanyaku_anten.csv"   # 三役暗転銘柄
    ichimoku_GC_under_cloud_csv_file_path = "C:\\Users\\mount\\Git\\StockAnalysis_Technical\\StockSignal\\Result\\ichimoku_GC_under_cloud.csv"   # 一目均衡表 雲の下でゴールデンクロス銘柄
    ichimoku_GC_upper_cloud_csv_file_path = "C:\\Users\\mount\\Git\\StockAnalysis_Technical\\StockSignal\\Result\\ichimoku_GC_upper_cloud.csv"   # 一目均衡表 雲の上でゴールデンクロス銘柄
    ichimoku_DC_under_cloud_csv_file_path = "C:\\Users\\mount\\Git\\StockAnalysis_Technical\\StockSignal\\Result\\ichimoku_DC_under_cloud.csv"   # 一目均衡表 雲の下でデッドクロス銘柄
    ichimoku_DC_upper_cloud_csv_file_path = "C:\\Users\\mount\\Git\\StockAnalysis_Technical\\StockSignal\\Result\\ichimoku_DC_upper_cloud.csv"   # 一目均衡表 雲の上でデッドクロス銘柄
    
    # 各CSVファイルを読み込んで、銘柄コード(Ticker)列で昇順ソートして再保存
    # 表示時に銘柄コードでソートされた状態にするため
    for file_path in [sanyaku_kouten_csv_file_path, sanyaku_anten_csv_file_path, ichimoku_GC_under_cloud_csv_file_path, ichimoku_GC_upper_cloud_csv_file_path, ichimoku_DC_under_cloud_csv_file_path, ichimoku_DC_upper_cloud_csv_file_path]:
        df = pd.read_csv(file_path, encoding='utf-8')    # CSVファイルを読み込み
        df_sorted = df.sort_values(by='Ticker')          # Ticker列で昇順ソート
        df_sorted.to_csv(file_path, index=False, encoding='utf-8')  # ソート結果を上書き保存
    
    # CSVデータをHTML表に変換（各テーブルの銘柄数も取得）
    html_table_sanyaku_kouten, sanyaku_kouten_count = read_csv_to_html_table(sanyaku_kouten_csv_file_path)   # 三役好転銘柄テーブル
    html_table_sanyaku_anten, sanyaku_anten_count = read_csv_to_html_table(sanyaku_anten_csv_file_path)   # 三役暗転銘柄テーブル
    html_table_ichimoku_GC_under_cloud, ichimoku_GC_under_cloud_count = read_csv_to_html_table(ichimoku_GC_under_cloud_csv_file_path)   # 雲の下でゴールデンクロス銘柄テーブル
    html_table_ichimoku_GC_upper_cloud, ichimoku_GC_upper_cloud_count = read_csv_to_html_table(ichimoku_GC_upper_cloud_csv_file_path)   # 雲の上でゴールデンクロス銘柄テーブル
    html_table_ichimoku_DC_under_cloud, ichimoku_DC_under_cloud_count = read_csv_to_html_table(ichimoku_DC_under_cloud_csv_file_path)   # 雲の下でデッドクロス銘柄テーブル
    html_table_ichimoku_DC_upper_cloud, ichimoku_DC_upper_cloud_count = read_csv_to_html_table(ichimoku_DC_upper_cloud_csv_file_path)   # 雲の上でデッドクロス銘柄テーブル
    
    # 投稿のタイトルと内容を作成
    post_title = "一目均衡表情報_{current_date}".format(current_date=current_date)  # 投稿タイトル
    
    # 投稿本文のHTML構成
    # WordPressテーマ「AFFINGER」用のスライドボックスブロックを使用
    # 初期状態では折りたたまれており、クリックで展開される
    post_content = f"""
        {intro_text}
        <h2>三役好転・三役暗転銘柄</h2>
        <h3>三役好転銘柄（{sanyaku_kouten_count}銘柄）</h3>
        <p><!-- wp:st-blocks/st-slidebox --></p>
        <div class="wp-block-st-blocks-st-slidebox st-slidebox-c is-collapsed has-st-toggle-icon is-st-toggle-position-left is-st-toggle-icon-position-left" data-st-slidebox="">
        <p class="st-btn-open" data-st-slidebox-toggle=""><i class="st-fa st-svg-plus-thin" data-st-slidebox-icon="" data-st-slidebox-icon-collapsed="st-svg-plus-thin" data-st-slidebox-icon-expanded="st-svg-minus-thin" aria-hidden=""></i><span class="st-slidebox-btn-text" data-st-slidebox-text="" data-st-slidebox-text-collapsed="クリックして展開" data-st-slidebox-text-expanded="閉じる">クリックして下さい</span></p>
        <div class="st-slidebox" data-st-slidebox-content="">
        <div class="scroll-box">
        三役好転銘柄テーブル
        {html_table_sanyaku_kouten}
        </div>
        </div>
        </div>
        <p><!-- /wp:st-blocks/st-slidebox --></p>
        
        <h3>三役暗転銘柄（{sanyaku_anten_count}銘柄）</h3>
        <p><!-- wp:st-blocks/st-slidebox --></p>
        <div class="wp-block-st-blocks-st-slidebox st-slidebox-c is-collapsed has-st-toggle-icon is-st-toggle-position-left is-st-toggle-icon-position-left" data-st-slidebox="">
        <p class="st-btn-open" data-st-slidebox-toggle=""><i class="st-fa st-svg-plus-thin" data-st-slidebox-icon="" data-st-slidebox-icon-collapsed="st-svg-plus-thin" data-st-slidebox-icon-expanded="st-svg-minus-thin" aria-hidden=""></i><span class="st-slidebox-btn-text" data-st-slidebox-text="" data-st-slidebox-text-collapsed="クリックして展開" data-st-slidebox-text-expanded="閉じる">クリックして下さい</span></p>
        <div class="st-slidebox" data-st-slidebox-content="">
        <div class="scroll-box">
        三役暗転銘柄テーブル
        {html_table_sanyaku_anten}
        </div>
        </div>
        </div>
        <p><!-- /wp:st-blocks/st-slidebox --></p>

        <h2>ゴールデンクロス銘柄</h2>
        <p>基準線と転換線がゴールデンクロスの状態となっている銘柄を抽出しています。</p>
        [st-mybox title="雲の上でのゴールデンクロス銘柄の条件" webicon="st-svg-check-circle" color="#03A9F4" bordercolor="#B3E5FC" bgcolor="#E1F5FE" borderwidth="2" borderradius="5" titleweight="bold"]
        <ol>
        <li>終値が雲の上にある</li>
        <li>基準線が転換線を上回った</li>
        <li>遅行線が終値の上にある</li>
        </ol>        
        <p>これは再び上昇トレンドに乗った銘柄を表しています。</p>
        <p></p>
        [/st-mybox]
        [st-mybox title="雲の下でのゴールデンクロス銘柄の条件" webicon="st-svg-check-circle" color="#03A9F4" bordercolor="#B3E5FC" bgcolor="#E1F5FE" borderwidth="2" borderradius="5" titleweight="bold"]
        <ol>
        <li>終値が雲の上にある</li>
        <li>基準線が転換線を上回った</li>
        <li>遅行線が終値の上にある</li>
        </ol>
        <p>これは上昇トレンドへの転換を示唆する銘柄を表しています。</p>
        <p></p>
        [/st-mybox]
        <p></p>
        <h3>雲の上でのゴールデンクロス銘柄（{ichimoku_GC_upper_cloud_count}銘柄）</h3>
        <p><!-- wp:st-blocks/st-slidebox --></p>
        <div class="wp-block-st-blocks-st-slidebox st-slidebox-c is-collapsed has-st-toggle-icon is-st-toggle-position-left is-st-toggle-icon-position-left" data-st-slidebox="">
        <p class="st-btn-open" data-st-slidebox-toggle=""><i class="st-fa st-svg-plus-thin" data-st-slidebox-icon="" data-st-slidebox-icon-collapsed="st-svg-plus-thin" data-st-slidebox-icon-expanded="st-svg-minus-thin" aria-hidden=""></i><span class="st-slidebox-btn-text" data-st-slidebox-text="" data-st-slidebox-text-collapsed="クリックして展開" data-st-slidebox-text-expanded="閉じる">クリックして下さい</span></p>
        <div class="st-slidebox" data-st-slidebox-content="">
        <div class="scroll-box">
        雲の上でのゴールデンクロス銘柄
        {html_table_ichimoku_GC_upper_cloud}
        </div>
        </div>
        </div>
        <p><!-- /wp:st-blocks/st-slidebox --></p>
        
        <h3>雲の下でのゴールデンクロス銘柄（{ichimoku_GC_under_cloud_count}銘柄）</h3>
        <p><!-- wp:st-blocks/st-slidebox --></p>
        <div class="wp-block-st-blocks-st-slidebox st-slidebox-c is-collapsed has-st-toggle-icon is-st-toggle-position-left is-st-toggle-icon-position-left" data-st-slidebox="">
        <p class="st-btn-open" data-st-slidebox-toggle=""><i class="st-fa st-svg-plus-thin" data-st-slidebox-icon="" data-st-slidebox-icon-collapsed="st-svg-plus-thin" data-st-slidebox-icon-expanded="st-svg-minus-thin" aria-hidden=""></i><span class="st-slidebox-btn-text" data-st-slidebox-text="" data-st-slidebox-text-collapsed="クリックして展開" data-st-slidebox-text-expanded="閉じる">クリックして下さい</span></p>
        <div class="st-slidebox" data-st-slidebox-content="">
        <div class="scroll-box">
        雲の下でのゴールデンクロス銘柄
        {html_table_ichimoku_GC_under_cloud}
        </div>
        </div>
        </div>
        <p><!-- /wp:st-blocks/st-slidebox --></p>

        <h2>デッドクロス銘柄</h2>
        <p>基準線と転換線がデッドクロスの状態となっている銘柄を抽出しています。</p>
        [st-mybox title="雲の下でのデッドクロス銘柄の条件" webicon="st-svg-check-circle" color="#03A9F4" bordercolor="#B3E5FC" bgcolor="#E1F5FE" borderwidth="2" borderradius="5" titleweight="bold"]
        <ol>
        <li>終値が雲の下にある</li>
        <li>基準線が転換線を下回った</li>
        <li>遅行線が終値の下にある</li>
        </ol>        
        <p>これは再び下降トレンドに乗った銘柄を表しています。</p>
        <p></p>
        [/st-mybox]
        [st-mybox title="雲の上でのデッドクロス銘柄の条件" webicon="st-svg-check-circle" color="#03A9F4" bordercolor="#B3E5FC" bgcolor="#E1F5FE" borderwidth="2" borderradius="5" titleweight="bold"]
        <ol>
        <li>終値が雲の上にある</li>
        <li>基準線が転換線を下回った</li>
        <li>遅行線が終値の下にある</li>
        </ol>
        <p>これは下降トレンドへの転換を示唆する銘柄を表しています。</p>
        <p></p>
        [/st-mybox]
        <p></p>
        <h3>雲の下でのデッドクロス銘柄（{ichimoku_DC_under_cloud_count}銘柄）</h3>
        <p><!-- wp:st-blocks/st-slidebox --></p>
        <div class="wp-block-st-blocks-st-slidebox st-slidebox-c is-collapsed has-st-toggle-icon is-st-toggle-position-left is-st-toggle-icon-position-left" data-st-slidebox="">
        <p class="st-btn-open" data-st-slidebox-toggle=""><i class="st-fa st-svg-plus-thin" data-st-slidebox-icon="" data-st-slidebox-icon-collapsed="st-svg-plus-thin" data-st-slidebox-icon-expanded="st-svg-minus-thin" aria-hidden=""></i><span class="st-slidebox-btn-text" data-st-slidebox-text="" data-st-slidebox-text-collapsed="クリックして展開" data-st-slidebox-text-expanded="閉じる">クリックして下さい</span></p>
        <div class="st-slidebox" data-st-slidebox-content="">
        <div class="scroll-box">
        雲の下でのゴールデンクロス銘柄
        {html_table_ichimoku_DC_under_cloud}
        </div>
        </div>
        </div>
        <p><!-- /wp:st-blocks/st-slidebox --></p>
        
        <h3>雲の上でのデッドクロス銘柄（{ichimoku_DC_upper_cloud_count}銘柄）</h3>
        <p><!-- wp:st-blocks/st-slidebox --></p>
        <div class="wp-block-st-blocks-st-slidebox st-slidebox-c is-collapsed has-st-toggle-icon is-st-toggle-position-left is-st-toggle-icon-position-left" data-st-slidebox="">
        <p class="st-btn-open" data-st-slidebox-toggle=""><i class="st-fa st-svg-plus-thin" data-st-slidebox-icon="" data-st-slidebox-icon-collapsed="st-svg-plus-thin" data-st-slidebox-icon-expanded="st-svg-minus-thin" aria-hidden=""></i><span class="st-slidebox-btn-text" data-st-slidebox-text="" data-st-slidebox-text-collapsed="クリックして展開" data-st-slidebox-text-expanded="閉じる">クリックして下さい</span></p>
        <div class="st-slidebox" data-st-slidebox-content="">
        <div class="scroll-box">
        雲の上でのデッドクロス銘柄
        {html_table_ichimoku_DC_upper_cloud}
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