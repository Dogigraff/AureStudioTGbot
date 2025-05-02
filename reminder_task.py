import asyncio
import datetime
from db import db
from config import ADMIN_CHAT_ID
from aiogram import Bot
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def send_reminders():
    bot = Bot(token=BOT_TOKEN)
    while True:
        leads = await db.get_unprocessed_leads_for_reminder(hours=1)
        for lead in leads:
            text = (
                f"❗️ <b>Новая заявка не обработана более 1 часа!</b>\n"
                f"Имя: {lead.get('name')}\n"
                f"Телефон: {lead.get('contact')}\n"
                f"E-mail: {lead.get('email', '-') }\n"
                f"Услуга: {lead.get('service', '-') }\n"
                f"Описание: {lead.get('description', '-') }\n"
                f"Создана: {lead.get('created')}\n"
                f"ID заявки: {lead.get('id')}"
            )
            await bot.send_message(ADMIN_CHAT_ID, text, parse_mode="HTML")
            await db.mark_lead_notified(lead.get('id'))
        await asyncio.sleep(600)  # 10 минут

if __name__ == "__main__":
    asyncio.run(send_reminders())
