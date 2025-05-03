import os
import json
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials

def export_lead_to_gsheet(name, contact, email, service, description):
    try:
        creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")  # JSON как строка
        creds_dict = json.loads(creds_json)  # Преобразуем в dict
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gc = gspread.authorize(creds)

        spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
        sheet_name = os.getenv("GOOGLE_SHEET_NAME")

        worksheet = gc.open_by_key(spreadsheet_id).worksheet(sheet_name)

        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        row = [name, contact, email, service, description, now]
        worksheet.append_row(row)

    except Exception as e:
        print(f"[Google Sheets] Не удалось экспортировать лид: {e}")
