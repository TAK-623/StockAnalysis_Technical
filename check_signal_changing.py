"""
シグナル変化検出スクリプト
このスクリプトは、株価シグナルの分析結果ファイルから、シグナルが変化した銘柄を抽出します。
テクニカル指標による売買シグナルおよび一目均衡表による売買シグナルの両方について、
前回と今回の状態が異なる銘柄を特定し、抽出結果をCSVファイルとして保存します。
"""
import pandas as pd

# 分析結果ファイルの読み込み
try:
    # 通常のテクニカル指標によるシグナル分析結果の読み込み
    # このファイルには銘柄ごとの売買シグナル（BUY/SELL/HOLD等）が含まれる
    result_df_signal = pd.read_csv('C:\\Users\\mount\\Git\\MyProject\\stockSignal\\Result.csv', encoding='utf-8')
    
    # 一目均衡表によるシグナル分析結果の読み込み
    # このファイルには一目均衡表の分析結果（三役好転/三役暗転等）が含まれる
    result_df_ichimoku = pd.read_csv('C:\\Users\\mount\\Git\\MyProject\\stockSignal\\Result_ichimoku.csv', encoding='utf-8')
except UnicodeDecodeError:
    # CSVファイルの文字エンコーディングが不適切な場合のエラー処理
    print("Error: CSVファイルのエンコーディングを確認してください。")

# シグナル変化の検出処理

# 通常のテクニカル指標シグナルについて、前回と今回の値を比較して異なる行を抽出
# カラム位置[2]は前回のシグナル値、カラム位置[3]は今回のシグナル値を表す
# 例: 前回HOLDだったものが今回BUYに変わった銘柄などを抽出
diff_df_signal = result_df_signal[result_df_signal.iloc[:, 2] != result_df_signal.iloc[:, 3]]

# 一目均衡表シグナルについて、前回と今回の値を比較して異なる行を抽出
# カラム位置[3]は前回の一目均衡表状態、カラム位置[4]は今回の一目均衡表状態を表す
# 例: 前回「雲の中」だったものが今回「雲の上」に変わった、または「三役好転」が発生した銘柄などを抽出
diff_df_ichimoku = result_df_ichimoku[result_df_ichimoku.iloc[:, 3] != result_df_ichimoku.iloc[:, 4]]

# 抽出結果をCSVファイルとして保存

# 通常のテクニカル指標シグナルの変化があった銘柄を保存
# このファイルは投資判断を支援するため、特に注目すべき銘柄リストとして使用される
diff_df_signal.to_csv('C:\\Users\\mount\\Git\\MyProject\\stockSignal\\Extract.csv', index=False, encoding='utf-8')

# 一目均衡表シグナルの変化があった銘柄を保存
# このファイルは一目均衡表特有のシグナル（三役好転/三役暗転など）が発生した銘柄リストとして使用される
diff_df_ichimoku.to_csv('C:\\Users\\mount\\Git\\MyProject\\stockSignal\\Extract_ichimoku.csv', index=False, encoding='utf-8')

# 処理完了の通知
print("比較と抽出が完了しました。")