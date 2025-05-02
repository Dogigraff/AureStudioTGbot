import asyncio
from db.db import init_db

async def clear_faq():
    await init_db()
    import aiosqlite
    async with aiosqlite.connect('db/db.sqlite3') as db:
        await db.execute('DELETE FROM faq')
        await db.commit()
        print('FAQ table cleared.')

if __name__ == "__main__":
    asyncio.run(clear_faq())
