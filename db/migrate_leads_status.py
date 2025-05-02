import aiosqlite
import asyncio

DB_PATH = '../ai_vision_studio.db'

async def migrate_leads_add_status_notified():
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute("ALTER TABLE leads ADD COLUMN status TEXT DEFAULT 'новая'")
        except Exception as e:
            print(f"status: {e}")
        try:
            await db.execute("ALTER TABLE leads ADD COLUMN notified INTEGER DEFAULT 0")
        except Exception as e:
            print(f"notified: {e}")
        await db.commit()

if __name__ == "__main__":
    asyncio.run(migrate_leads_add_status_notified())
