import gspread
from google.oauth2.service_account import Credentials
import os
from datetime import datetime

CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "google-credentials.json")
SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME_REVIEWS", "AI Vision Reviews")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def export_review_to_gsheet(username, user_id, review_text):
    creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
    gc = gspread.authorize(creds)
    # Если отдельная таблица для отзывов не нужна, используйте sheet2 в AI Vision Leads
    try:
        sheet = gc.open(SHEET_NAME).sheet1
    except Exception:
        # Если такой таблицы нет, fallback: создаём второй лист в основной таблице
        sheet = gc.open(os.getenv("GOOGLE_SHEET_NAME", "AI Vision Leads")).add_worksheet(title="Reviews", rows="100", cols="10")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    row = [now, username, user_id, review_text]
    sheet.append_row(row)
