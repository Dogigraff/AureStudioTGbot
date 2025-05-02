import csv
from db.db import get_leads

EXPORT_FILE = "leads_export.csv"

async def export_leads_to_csv() -> str:
    leads = await get_leads()
    if not leads:
        return None
    with open(EXPORT_FILE, "w", newline='', encoding="utf-8") as csvfile:
        fieldnames = ["id", "user_id", "name", "contact", "service", "description", "photo", "created"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for lead in leads:
            writer.writerow(lead)
    return EXPORT_FILE
