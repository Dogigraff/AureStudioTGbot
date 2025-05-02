import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Жёстко прописанные параметры (можно вынести в конфиг при необходимости)
CREDENTIALS_FILE = "ai-vision-leads-4c6f5fbe4a8c.json"
SPREADSHEET_ID = "1dTca6TSFPLfb6aN4EtznpDQFoxo-fUhatykHfYvckVY"
SHEET_NAME = "Лист1"  # имя листа, как в вашей таблице

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def export_lead_to_gsheet(name, contact, email, service, description):
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    worksheet = sh.worksheet(SHEET_NAME)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    row = [name, contact, email, service, description, now]
    worksheet.append_row(row)
