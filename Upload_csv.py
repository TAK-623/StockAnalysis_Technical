from __future__ import print_function
import os.path
import pandas as pd
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/spreadsheets']

def create_folder(service, folder_name, parent_folder_id=None):
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_folder_id:
        file_metadata['parents'] = [parent_folder_id]
    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder.get('id')

def upload_file(service, file_path, folder_id):
    file_name = os.path.basename(file_path)  # フルパスからファイル名のみを抽出
    file_metadata = {'name': file_name, 'parents': [folder_id]}
    media = MediaFileUpload(file_path, mimetype='text/csv')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"File ID: {file.get('id')}")
    return file.get('id')

def convert_to_google_sheet(service, file_id, sheet_name):
    file_metadata = {
        'name': sheet_name,
        'mimeType': 'application/vnd.google-apps.spreadsheet'
    }
    drive_response = service.files().copy(fileId=file_id, body=file_metadata).execute()
    return drive_response.get('id')

def get_sheet_id(spreadsheet_service, spreadsheet_id, sheet_name):
    # スプレッドシート情報を取得
    spreadsheet = spreadsheet_service.get(spreadsheetId=spreadsheet_id).execute()
    # シート情報を取得してシート名に一致するものを探す
    for sheet in spreadsheet['sheets']:
        if sheet['properties']['title'] == sheet_name:
            return sheet['properties']['sheetId']
    raise ValueError(f"Sheet name '{sheet_name}' not found.")

def sort_spreadsheet(spreadsheet_service, spreadsheet_id, sheet_name):
    # シートIDを取得
    grid_id = get_sheet_id(spreadsheet_service, spreadsheet_id, sheet_name)

    # 並べ替えの設定
    sort_request = {
        "requests": [
            {
                "sortRange": {
                    "range": {
                        "sheetId": grid_id,  # 動的に取得したシートIDを使用
                        "startRowIndex": 1,  # 並べ替え開始行（ヘッダーを除く場合1以上）
                    },
                    "sortSpecs": [
                        {
                            "dimensionIndex": 2,  # 並べ替え基準列（0始まりの列番号）
                            "sortOrder": "ASCENDING"  # 昇順
                        }
                    ]
                }
            }
        ]
    }
    # リクエストを送信して並べ替えを実行
    response = spreadsheet_service.batchUpdate(spreadsheetId=spreadsheet_id, body=sort_request).execute()
    print("並べ替えが完了しました。")

def main():
    """Shows basic usage of the Drive v3 API.
    Uploads files to Google Drive and converts them to Google Sheets.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('C:\\Users\\mount\\Git\\MyProject\\stockSignal\\token.json'):
        creds = Credentials.from_authorized_user_file('C:\\Users\\mount\\Git\\MyProject\\stockSignal\\token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'C:\\Users\\mount\\Git\\MyProject\\stockSignal\\credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)  # ここでポート番号を指定
        # Save the credentials for the next run
        with open('C:\\Users\\mount\\Git\\MyProject\\stockSignal\\token.json', 'w') as token:
            token.write(creds.to_json())

    drive_service = build('drive', 'v3', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)

    # "株"フォルダのIDを取得（事前に作成しておく必要があります）
    KABU_FOLDER_ID = '14dKMMuKFQu9cgRw-UQeY2UK_fLDnwvOz'  # ここに"株"フォルダのIDを入れてください

    # "yyyymmdd"フォルダを作成
    today_str = datetime.datetime.today().strftime('%Y%m%d')
    yyyymmdd_folder_id = create_folder(drive_service, today_str, KABU_FOLDER_ID)

    # ファイルのアップロードとGoogleスプレッドシートへの変換(並び替えありファイル)
    files_to_upload = [
        'C:\\Users\\mount\\Git\\MyProject\\stockSignal\\Result.csv',
        'C:\\Users\\mount\\Git\\MyProject\\stockSignal\\Extract.csv',
        'C:\\Users\\mount\\Git\\MyProject\\stockSignal\\Result_ichimoku.csv',
        'C:\\Users\\mount\\Git\\MyProject\\stockSignal\\Extract_ichimoku.csv',
    ]
    for file_path in files_to_upload:
        file_id = upload_file(drive_service, file_path, yyyymmdd_folder_id)
        sheet_name = os.path.splitext(os.path.basename(file_path))[0]  # 拡張子を除いたファイル名をシート名として使用
        sheet_id = convert_to_google_sheet(drive_service, file_id, sheet_name)
        print(f"Google Sheet ID for {sheet_name}: {sheet_id}")
        sort_spreadsheet(sheets_service.spreadsheets(), sheet_id, sheet_name)
    # ファイルのアップロードとGoogleスプレッドシートへの変換(並び替え不要ファイル)
    files_to_upload_no_sort = [
        'C:\\Users\\mount\\Git\\MyProject\\stockSignal\\Result_detail.csv',
        # "C:\\Users\\mount\\Git\\MyProject\\stockSignal\\ichimoku_for_blog.csv",
        'C:\\Users\\mount\\Git\\MyProject\\stockSignal\\ichimoku_for_blog_kouten.csv',
        'C:\\Users\\mount\\Git\\MyProject\\stockSignal\\ichimoku_for_blog_anten.csv',
        'C:\\Users\\mount\\Git\\MyProject\\stockSignal\\ichimoku_for_blog_kouten_start.csv',
        'C:\\Users\\mount\\Git\\MyProject\\stockSignal\\ichimoku_for_blog_anten_start.csv',
        'C:\\Users\\mount\\Git\\MyProject\\stockSignal\\ichimoku_for_blog_kouten_end.csv',
        'C:\\Users\\mount\\Git\\MyProject\\stockSignal\\ichimoku_for_blog_anten_end.csv',
    ]
    for file_path in files_to_upload_no_sort:
        file_id = upload_file(drive_service, file_path, yyyymmdd_folder_id)
        sheet_name = os.path.splitext(os.path.basename(file_path))[0]  # 拡張子を除いたファイル名をシート名として使用
        sheet_id = convert_to_google_sheet(drive_service, file_id, sheet_name)
        print(f"Google Sheet ID for {sheet_name}: {sheet_id}")

if __name__ == '__main__':
    main()
    print("ファイルのアップロードとGoogleスプレッドシートへのインポートが完了しました。")
