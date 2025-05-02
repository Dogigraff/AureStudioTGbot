import csv
import os
from db.db import get_users_count
from datetime import datetime

async def export_users_to_csv(get_all_users_func):
    users = await get_all_users_func()
    if not users:
        return None
    filename = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    path = os.path.join(os.getcwd(), filename)
    with open(path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["User ID", "Username", "Full Name", "Дата регистрации"])
        for u in users:
            writer.writerow([
                u.get("tg_id", ""),
                u.get("username", ""),
                u.get("full_name", ""),
                u.get("created", "")
            ])
    return path
