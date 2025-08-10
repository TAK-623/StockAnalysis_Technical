"""
WordPress投稿モジュール

このモジュールは以下の機能を提供します：
1. 既存のUpload_WardPress.pyの機能を拡張
2. 生成されたチャートをWordPress記事に追加
3. レンジブレイク銘柄のチャートを記事に埋め込み
"""

import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import os
import base64

class WordPressPoster:
    """
    WordPress投稿クラス
    """
    
    def __init__(self):
        """
        初期化
        """
        # WordPressサイトの接続情報を設定
        self.WP_SITE_URL = "https://www.takstorage.site/"
        self.WP_API_ENDPOINT = f"{self.WP_SITE_URL}/wp-json/wp/v2/posts"
        self.WP_USERNAME = "tak.note7120@gmail.com"
        self.WP_APP_PASSWORD = "GNrk aQ3d 7GWu p1fw dCfM pAGH"
        
        # ファイルパスの設定
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.range_break_file = os.path.join(self.base_dir, "Result", "Range_Brake.csv")
        
        # 今日の日付を取得
        self.current_date = datetime.now().strftime("%Y/%m/%d")
    
    def read_csv_to_html_table(self, csv_file_path):
        """
        CSVファイルを読み込み、スタイリングされたHTML表に変換
        
        Args:
            csv_file_path (str): 読み込むCSVファイルのパス
            
        Returns:
            tuple: (スタイル適用済みのHTML表, 銘柄数)
        """
        try:
            # CSVファイルをpandasデータフレームとして読み込み
            df = pd.read_csv(csv_file_path)
            
            # 数値フォーマットをカスタマイズする関数
            def format_number(x):
                if pd.isna(x):
                    return x
                
                try:
                    num_value = float(x)
                    if num_value.is_integer():
                        return int(num_value)
                    else:
                        return f"{num_value:.1f}"
                except (ValueError, TypeError):
                    return x
            
            # 各列のデータタイプを確認し、数値列に対してフォーマット適用
            for col in df.columns:
                if df[col].dtype in ['int64', 'float64']:
                    df[col] = df[col].apply(format_number)
            
            # DataFrame を HTML テーブルに変換
            df_html = df.to_html(index=False, border=1, escape=False)
            
            # 銘柄名（Name列）が長い場合でもテーブルレイアウトを崩さないようにスタイル適用
            df_html = df_html.replace('<th>', '<th style="max-width:800px; white-space:nowrap; overflow:hidden;">')
            df_html = df_html.replace('<td>', '<td style="max-width:800px; word-wrap:break-word;">')
            
            # テーブルをスクロール可能なdivコンテナでラップ
            styled_table = f"""
            <div class="scroll-box">
                {df_html}
            </div>
            """
            
            return styled_table, len(df)
            
        except Exception as e:
            print(f"CSVファイルの読み込みエラー: {e}")
            return "", 0
    
    def create_chart_html(self, chart_paths):
        """
        チャート画像のHTMLを生成
        
        Args:
            chart_paths (list): チャートファイルのパスリスト
            
        Returns:
            str: チャート画像のHTML
        """
        chart_html = ""
        
        for chart_path in chart_paths:
            try:
                # ファイル名からティッカーを抽出
                filename = os.path.basename(chart_path)
                ticker = filename.replace('_chart.png', '')
                
                # 画像をbase64エンコード
                with open(chart_path, 'rb') as img_file:
                    img_data = base64.b64encode(img_file.read()).decode('utf-8')
                
                # HTMLを生成
                chart_html += f"""
                <div style="margin: 20px 0; text-align: center;">
                    <h4>{ticker} のチャート</h4>
                    <img src="data:image/png;base64,{img_data}" 
                         alt="{ticker} チャート" 
                         style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px;">
                </div>
                """
                
            except Exception as e:
                print(f"チャートHTML生成エラー ({chart_path}): {e}")
        
        return chart_html
    
    def post_to_wordpress(self, title, post_content):
        """
        WordPressに投稿記事を送信
        
        Args:
            title (str): 投稿のタイトル
            post_content (str): 投稿の本文（HTMLフォーマット）
        """
        # 投稿データの構成
        post_data = {
            "title": title,
            "content": post_content,
            "status": "publish",
            "categories": [22],
            "tags": [19],
            "featured_media": 809
        }
        
        # WordPress REST APIにリクエストを送信
        response = requests.post(
            self.WP_API_ENDPOINT,
            json=post_data,
            auth=HTTPBasicAuth(self.WP_USERNAME, self.WP_APP_PASSWORD)
        )
        
        # レスポンスを確認して結果をコンソールに表示
        if response.status_code == 201:
            print("投稿が成功しました:", response.json()["link"])
        else:
            print("投稿に失敗しました:", response.status_code, response.text)
    
    def post_with_charts(self, chart_paths):
        """
        チャート付きでWordPressに投稿
        
        Args:
            chart_paths (list): チャートファイルのパスリスト
        """
        try:
            # レンジブレイク銘柄のテーブルを読み込み
            html_table_range_break, range_break_count = self.read_csv_to_html_table(self.range_break_file)
            
            # チャートのHTMLを生成
            chart_html = self.create_chart_html(chart_paths)
            
            # 投稿の冒頭部分のテキスト
            intro_text = f"""
            <p>{self.current_date}終わり時点での情報です。</p>
            <p>Pythonを使用して自動でデータ収集&演算を行い、レンジをブレイクした銘柄を抽出しています。</p>
            <p>銘柄名に付いているアルファベットで市場を表しています。</p>
            <div class="graybox">
            <p>P: プライム市場の銘柄</p>
            <p>S: スタンダード市場の銘柄</p>
            <p>G: グロース市場の銘柄</p>
            </div>
            <p></p>
            <p>レンジブレイク銘柄は、直近1か月の高値をブレイクした銘柄を挙げています。</p>
            <p></p>
            """
            
            # 投稿のタイトルと内容を作成
            post_title = f"レンジブレイク銘柄チャート_{self.current_date}"
            
            # 投稿本文のHTML構成
            post_content = f"""
            {intro_text}
            
            <h2>レンジブレイク銘柄 ({range_break_count}銘柄)</h2>
            <p>過去3か月間の最高値を更新した銘柄です。</p>
            <p>下記の条件で抽出しています。</p>
            <div style="background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin: 15px 0;">
            <h4>レンジブレイク銘柄を抽出する条件</h4>
            <ol>
            <li>最新の終値が過去3か月間の最高値を上回っている</li>
            <li>最新の出来高が過去3か月間の出来高平均値の1.5倍よりも多い</li>
            <li>終値が高値と安値の中間値よりも高い</li>
            <li>最新の出来高が10万以上</li>
            </ol>
            </div>
            
            <h3>レンジブレイク銘柄一覧</h3>
            <div class="wp-block-st-blocks-st-slidebox st-slidebox-c is-collapsed has-st-toggle-icon is-st-toggle-position-left is-st-toggle-icon-position-left" data-st-slidebox="">
            <p class="st-btn-open" data-st-slidebox-toggle=""><i class="st-fa st-svg-plus-thin" data-st-slidebox-icon="" data-st-slidebox-icon-collapsed="st-svg-plus-thin" data-st-slidebox-icon-expanded="st-svg-minus-thin" aria-hidden=""></i><span class="st-slidebox-btn-text" data-st-slidebox-text="" data-st-slidebox-text-collapsed="クリックして展開" data-st-slidebox-text-expanded="閉じる">クリックして下さい</span></p>
            <div class="st-slidebox" data-st-slidebox-content="">
            <div class="scroll-box">
            レンジブレイク銘柄
            {html_table_range_break}
            </div>
            </div>
            </div>
            
            <h2>レンジブレイク銘柄チャート</h2>
            <p>各銘柄の株価チャートです。過去60日間の価格推移と出来高を表示しています。</p>
            
            {chart_html}
            """
            
            # WordPressに投稿を送信
            self.post_to_wordpress(post_title, post_content)
            
        except Exception as e:
            print(f"WordPress投稿エラー: {e}")

