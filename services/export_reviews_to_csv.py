import csv
import os
from db.db import get_reviews
from datetime import datetime

async def export_reviews_to_csv():
    reviews = await get_reviews(limit=10000)  # выгружаем все
    if not reviews:
        return None
    filename = f"reviews_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    path = os.path.join(os.getcwd(), filename)
    with open(path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Дата", "User ID", "Username", "Текст"])
        for r in reviews:
            writer.writerow([
                r.get("created", ""),
                r.get("user_id", ""),
                r.get("username", ""),
                r.get("text", "")
            ])
    return path
