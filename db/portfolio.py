import aiosqlite
from typing import List, Dict

DB_PATH = 'ai_vision_studio.db'

async def add_portfolio_item(author_id: int, title: str, description: str = None, photo: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('INSERT INTO portfolio (author_id, title, description, photo) VALUES (?, ?, ?, ?)',
                         (author_id, title, description, photo))
        await db.commit()

async def get_portfolio(limit: int = 10) -> List[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT * FROM portfolio ORDER BY id DESC LIMIT ?', (limit,)) as cursor:
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) async for row in cursor]
