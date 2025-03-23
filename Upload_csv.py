"""
Google Drive APIを使用して分析結果CSVファイルをアップロードおよびスプレッドシート化するスクリプト

このスクリプトは以下の機能を提供します：
1. Google Driveに接続してフォルダを作成
2. CSVファイルをGoogle Driveにアップロード
3. アップロードしたCSVファイルをGoogleスプレッドシートに変換
4. 必要に応じてスプレッドシートの内容を特定の列でソート
"""
from __future__ import print_function
import os.path
import pandas as pd
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Google APIのスコープ定義
# SCOPES変更時はtoken.jsonを削除する必要があります（再認証が必要になるため）
SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/spreadsheets']

def create_folder(service, folder_name, parent_folder_id=None):
    """
    Google Drive上にフォルダを作成します
    
    Args:
        service: Google Drive APIサービスオブジェクト
        folder_name: 作成するフォルダ名
        parent_folder_id: 親フォルダのID（指定がない場合はルートに作成）
    
    Returns:
        str: 作成されたフォルダのID
    """
    # フォルダ作成のためのメタデータを設定
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'  # フォルダタイプを指定
    }
    
    # 親フォルダが指定されている場合は、その配下に作成
    if parent_folder_id:
        file_metadata['parents'] = [parent_folder_id]
    
    # フォルダ作成APIを呼び出し
    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder.get('id')  # 作成されたフォルダのIDを返す

def upload_file(service, file_path, folder_id):
    """
    ファイルをGoogle Driveの指定フォルダにアップロードします
    
    Args:
        service: Google Drive APIサービスオブジェクト
        file_path: アップロードするファイルのローカルパス
        folder_id: アップロード先フォルダのID
    
    Returns:
        str: アップロードされたファイルのID
    """
    # ファイルパスからファイル名のみを抽出
    file_name = os.path.basename(file_path)
    
    # アップロードするファイルのメタデータを設定
    file_metadata = {
        'name': file_name,  # Google Drive上でのファイル名
        'parents': [folder_id]  # アップロード先フォルダ
    }
    
    # ファイルのメディアタイプ（MIME Type）を指定してアップロード用オブジェクトを作成
    media = MediaFileUpload(file_path, mimetype='text/csv')
    
    # ファイルアップロードAPIを呼び出し
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"File ID: {file.get('id')}")  # アップロードされたファイルのIDを表示
    
    return file.get('id')  # アップロードされたファイルのIDを返す

def convert_to_google_sheet(service, file_id, sheet_name):
    """
    アップロードしたCSVファイルをGoogleスプレッドシートに変換します
    
    Args:
        service: Google Drive APIサービスオブジェクト
        file_id: 変換するCSVファイルのID
        sheet_name: 作成するスプレッドシートの名前
    
    Returns:
        str: 作成されたGoogleスプレッドシートのID
    """
    # スプレッドシート変換のためのメタデータを設定
    file_metadata = {
        'name': sheet_name,  # スプレッドシート名
        'mimeType': 'application/vnd.google-apps.spreadsheet'  # スプレッドシートタイプを指定
    }
    
    # ファイルコピーAPIを使用して、CSVをスプレッドシートとしてコピー（変換）
    drive_response = service.files().copy(fileId=file_id, body=file_metadata).execute()
    return drive_response.get('id')  # 作成されたスプレッドシートのIDを返す

def get_sheet_id(spreadsheet_service, spreadsheet_id, sheet_name):
    """
    スプレッドシート内の特定シートのIDを取得します
    
    Args:
        spreadsheet_service: Google Sheets APIサービスオブジェクト
        spreadsheet_id: スプレッドシートのID
        sheet_name: 取得するシートの名前
    
    Returns:
        int: シートのID
    
    Raises:
        ValueError: 指定されたシート名が見つからない場合
    """
    # スプレッドシート情報を取得
    spreadsheet = spreadsheet_service.get(spreadsheetId=spreadsheet_id).execute()
    
    # スプレッドシート内の全シートをループして、指定された名前のシートを探す
    for sheet in spreadsheet['sheets']:
        if sheet['properties']['title'] == sheet_name:
            return sheet['properties']['sheetId']  # 見つかったシートのIDを返す
    
    # 指定されたシート名が見つからない場合はエラー
    raise ValueError(f"Sheet name '{sheet_name}' not found.")

def sort_spreadsheet(spreadsheet_service, spreadsheet_id, sheet_name):
    """
    スプレッドシートの内容を特定の列でソートします
    
    Args:
        spreadsheet_service: Google Sheets APIサービスオブジェクト
        spreadsheet_id: ソート対象のスプレッドシートID
        sheet_name: ソート対象のシート名
    """
    # シートIDを取得（各シートには固有のIDが割り当てられている）
    grid_id = get_sheet_id(spreadsheet_service, spreadsheet_id, sheet_name)

    # ソート処理のリクエスト内容を定義
    sort_request = {
        "requests": [
            {
                "sortRange": {
                    "range": {
                        "sheetId": grid_id,  # 動的に取得したシートIDを使用
                        "startRowIndex": 1,  # ソート開始行（ヘッダー行を除く場合は1以上）
                    },
                    "sortSpecs": [
                        {
                            "dimensionIndex": 2,  # ソート基準列（0始まりのインデックス、3列目を表す）
                            "sortOrder": "ASCENDING"  # ソート順（昇順）
                        }
                    ]
                }
            }
        ]
    }
    
    # バッチ更新APIを呼び出してソート処理を実行
    response = spreadsheet_service.batchUpdate(spreadsheetId=spreadsheet_id, body=sort_request).execute()
    print("並べ替えが完了しました。")

def main():
    """
    メイン処理：Google Drive APIの認証、ファイルのアップロード、スプレッドシート変換を行います
    """
    creds = None
    
    # token.jsonファイルから認証情報を読み込む
    # このファイルは初回認証時に自動的に作成され、以降の認証に使用される
    if os.path.exists('C:\\Users\\mount\\Git\\StockSignal\\token.json'):
        creds = Credentials.from_authorized_user_file('C:\\Users\\mount\\Git\\StockSignal\\token.json', SCOPES)
    
    # 有効な認証情報が無い場合は、ユーザーにログインを要求
    if not creds or not creds.valid:
        # 有効期限切れの認証情報があり、リフレッシュトークンがある場合は更新
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # 新規認証フローを開始
            flow = InstalledAppFlow.from_client_secrets_file(
                'C:\\Users\\mount\\Git\\StockSignal\\credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)  # ローカルWebサーバーでOAuth認証（ポート8080使用）
        
        # 次回使用のために認証情報を保存
        with open('C:\\Users\\mount\\Git\\StockSignal\\token.json', 'w') as token:
            token.write(creds.to_json())

    # Google Drive APIとGoogle Sheets APIのサービスオブジェクトを構築
    drive_service = build('drive', 'v3', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)

    # "株"フォルダのID（Google Drive上に事前に作成済みのフォルダ）
    KABU_FOLDER_ID = '14dKMMuKFQu9cgRw-UQeY2UK_fLDnwvOz'
    
    # 今日の日付をYYYYMMDD形式で取得し、その名前のフォルダを作成
    today_str = datetime.datetime.today().strftime('%Y%m%d')
    yyyymmdd_folder_id = create_folder(drive_service, today_str, KABU_FOLDER_ID)

    # アップロードして並べ替えを行うファイルリスト
    # 現在はコメントアウトされているため、処理されない
    files_to_upload = [
        # 'C:\\Users\\mount\\Git\\MyProject\\stockSignal\\Result.csv',
        # 'C:\\Users\\mount\\Git\\MyProject\\stockSignal\\Extract.csv',
        # 'C:\\Users\\mount\\Git\\MyProject\\stockSignal\\Result_ichimoku.csv',
        # 'C:\\Users\\mount\\Git\\MyProject\\stockSignal\\Extract_ichimoku.csv',
    ]
    
    # 各ファイルについて処理：アップロード→スプレッドシート変換→ソート
    for file_path in files_to_upload:
        # ファイルをアップロード
        file_id = upload_file(drive_service, file_path, yyyymmdd_folder_id)
        
        # ファイル名から拡張子を除いた部分をシート名として使用
        sheet_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # スプレッドシートに変換
        sheet_id = convert_to_google_sheet(drive_service, file_id, sheet_name)
        print(f"Google Sheet ID for {sheet_name}: {sheet_id}")
        
        # スプレッドシートの内容をソート
        sort_spreadsheet(sheets_service.spreadsheets(), sheet_id, sheet_name)
    
    # アップロードするが並べ替えは行わないファイルリスト
    # シグナル結果（買い・売り）のCSVファイル
    files_to_upload_no_sort = [
        'C:\\Users\\mount\\Git\\StockSignal\\Result\\macd_rsi_signal_result_buy.csv',  # 買いシグナルCSV
        'C:\\Users\\mount\\Git\\StockSignal\\Result\\macd_rsi_signal_result_sell.csv', # 売りシグナルCSV
        'C:\\Users\\mount\\Git\\StockSignal\\Result\\macd_rci_signal_result_buy.csv',  # 買いシグナルCSV
        'C:\\Users\\mount\\Git\\StockSignal\\Result\\macd_rci_signal_result_sell.csv', # 売りシグナルCSV
        'C:\\Users\\mount\\Git\\StockSignal\\Result\\macd_rsi_rci_signal_result_buy.csv',  # 買いシグナルCSV
        'C:\\Users\\mount\\Git\\StockSignal\\Result\\macd_rsi_rci_signal_result_sell.csv', # 売りシグナルCSV
        'C:\\Users\\mount\\Git\\StockSignal\\TechnicalSignal\\latest_signal.csv', # テクニカル指標最新値CSV
    ]
    
    # 各ファイルについて処理：アップロード→スプレッドシート変換（ソートなし）
    for file_path in files_to_upload_no_sort:
        # ファイルをアップロード
        file_id = upload_file(drive_service, file_path, yyyymmdd_folder_id)
        
        # ファイル名から拡張子を除いた部分をシート名として使用
        sheet_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # スプレッドシートに変換
        sheet_id = convert_to_google_sheet(drive_service, file_id, sheet_name)
        print(f"Google Sheet ID for {sheet_name}: {sheet_id}")

# スクリプトが直接実行された場合のエントリーポイント
if __name__ == '__main__':
    main()  # メイン処理を実行
    print("ファイルのアップロードとGoogleスプレッドシートへのインポートが完了しました。")  # 完了メッセージ