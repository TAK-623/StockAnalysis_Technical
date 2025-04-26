import pandas as pd
import datetime as dt

def process_excel():
    # 1. 同じディレクトリにあるdata_j.xlsxを読み込む
    file_path = "data_j.xlsx"
    df = pd.read_excel(file_path)
    
    # データ構造を確認
    print(f"元のデータ行数: {len(df)}")
    
    # 2. B1セル（"コード"）を"Ticker"に変更する
    df.rename(columns={"コード": "Ticker"}, inplace=True)
    
    # 市場区分列の名前を確認
    market_column = "市場・商品区分"  # 正確な列名を使用
    
    # 33業種区分の列名を確認（実際の列名に合わせて変更する必要があるかもしれません）
    industry_column = "33業種区分"
    
    # 3. 指定された市場区分のみを抽出
    target_markets = ["プライム（内国株式）", "スタンダード（内国株式）", "グロース（内国株式）"]
    filtered_df = df[df[market_column].isin(target_markets)].copy()
    
    print(f"フィルタリング後のデータ行数: {len(filtered_df)}")
    print(f"除外された行数: {len(df) - len(filtered_df)}")
    
    # フィルタリング後の市場区分の確認
    filtered_markets = filtered_df[market_column].unique()
    print(f"フィルタリング後の市場区分: {filtered_markets}")
    
    # 全角英数を半角英数に変換する関数
    def zen_to_han(text):
        if isinstance(text, str):
            # 全角英数字を半角に変換
            zen = "０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ（）．，－：　"
            han = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz().,-: "
            trans_table = str.maketrans(zen, han)
            return text.translate(trans_table)
        return text
    
    # 銘柄名の全角英数を半角に変換
    filtered_df["銘柄名"] = filtered_df["銘柄名"].apply(zen_to_han)
    
    # 4. 市場区分に基づいて銘柄名のテキストを変更
    for idx, row in filtered_df.iterrows():
        market_category = row[market_column]
        company_name = row["銘柄名"]
        
        if market_category == "プライム（内国株式）":
            filtered_df.at[idx, "銘柄名"] = f"P: {company_name}"
        elif market_category == "スタンダード（内国株式）":
            filtered_df.at[idx, "銘柄名"] = f"S: {company_name}"
        elif market_category == "グロース（内国株式）":
            filtered_df.at[idx, "銘柄名"] = f"G: {company_name}"
    
    # 5. 必要な列のみを抽出してCSVファイルに保存（元のファイル）
    result_df = filtered_df[["Ticker", "銘柄名"]]
    
    # 現在の日付を取得してファイル名を生成（YYYYMMDDフォーマット）
    today = dt.datetime.now().strftime("%Y%m%d")
    output_filename = f"company_list_{today}.csv"
    
    # CSVファイルに保存（日本語を正しく表示するためにUTF-8エンコーディングを使用）
    result_df.to_csv(output_filename, index=False, encoding='utf-8')
    
    print(f"\n処理が完了しました。ファイル '{output_filename}' が作成されました。")
    print(f"抽出された会社数: {len(result_df)}")
    
    # 6. 新たに業種情報を含めたCSVファイルも作成
    industry_df = filtered_df[["Ticker", "銘柄名", industry_column]]
    industry_output_filename = f"company_industry_list_{today}.csv"
    
    # CSVファイルに保存
    industry_df.to_csv(industry_output_filename, index=False, encoding='utf-8')
    
    print(f"\n追加の処理が完了しました。ファイル '{industry_output_filename}' が作成されました。")
    print(f"抽出された会社数（業種情報付き）: {len(industry_df)}")

if __name__ == "__main__":
    process_excel()