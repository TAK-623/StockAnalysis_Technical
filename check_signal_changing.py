import pandas as pd

# result.csvの読み込み
try:
    result_df_signal = pd.read_csv('C:\\Users\\mount\\Git\\MyProject\\stockSignal\\Result.csv', encoding='utf-8')  # エンコーディングを適宜指定
    result_df_ichimoku = pd.read_csv('C:\\Users\\mount\\Git\\MyProject\\stockSignal\\Result_ichimoku.csv', encoding='utf-8')  # エンコーディングを適宜指定
except UnicodeDecodeError:
    print("Error: CSVファイルのエンコーディングを確認してください。")

# 比較して異なる値を持つ行を抽出
diff_df_signal = result_df_signal[result_df_signal.iloc[:, 2] != result_df_signal.iloc[:, 3]]
diff_df_ichimoku = result_df_ichimoku[result_df_ichimoku.iloc[:, 3] != result_df_ichimoku.iloc[:, 4]]

# extract.csvに出力
diff_df_signal.to_csv('C:\\Users\\mount\\Git\\MyProject\\stockSignal\\Extract.csv', index=False, encoding='utf-8')  # エンコーディングを適宜指定
diff_df_ichimoku.to_csv('C:\\Users\\mount\\Git\\MyProject\\stockSignal\\Extract_ichimoku.csv', index=False, encoding='utf-8')  # エンコーディングを適宜指定

print("比較と抽出が完了しました。")
