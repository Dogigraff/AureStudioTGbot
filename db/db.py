import aiosqlite
from typing import Optional, List, Dict, Any
import datetime

DB_PATH = 'ai_vision_studio.db'

# ... (остальной код)

async def get_unprocessed_leads_for_reminder(hours: int = 1) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        cutoff = (datetime.datetime.utcnow() - datetime.timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        query = '''SELECT * FROM leads WHERE status = 'новая' AND notified = 0 AND created < ?'''
        async with db.execute(query, (cutoff,)) as cursor:
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) async for row in cursor]

async def mark_lead_notified(lead_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE leads SET notified=1 WHERE id=?', (lead_id,))
        await db.commit()

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            tg_id INTEGER UNIQUE,
            username TEXT,
            full_name TEXT,
            subscribed INTEGER DEFAULT 1
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            contact TEXT,
            service TEXT,
            description TEXT,
            photo TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author_id INTEGER,
            text TEXT,
            photo TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author_id INTEGER,
            title TEXT,
            description TEXT,
            photo TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            text TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS faq (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            answer TEXT
        )''')
        await db.commit()

async def add_user(tg_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''INSERT OR IGNORE INTO users (tg_id, username, full_name) VALUES (?, ?, ?)''',
                         (tg_id, username, full_name))
        await db.commit()

async def set_user_subscribed(tg_id: int, subscribed: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE users SET subscribed=? WHERE tg_id=?', (subscribed, tg_id))
        await db.commit()

async def get_all_subscribed_users() -> List[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT tg_id FROM users WHERE subscribed=1') as cursor:
            return [row[0] async for row in cursor]

async def add_lead(user_id: int, name: str, contact: str, service: str, description: str, photo: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''INSERT INTO leads (user_id, name, contact, service, description, photo) VALUES (?, ?, ?, ?, ?, ?)''',
                         (user_id, name, contact, service, description, photo))
        await db.commit()

async def get_leads() -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT * FROM leads ORDER BY created DESC') as cursor:
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) async for row in cursor]

async def get_new_leads() -> List[Dict[str, Any]]:
    """Вернуть только новые лиды (status = 'новая')."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM leads WHERE status = 'новая' ORDER BY created DESC") as cursor:
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) async for row in cursor]

async def add_post(author_id: int, text: str = None, photo: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('INSERT INTO posts (author_id, text, photo) VALUES (?, ?, ?)', (author_id, text, photo))
        await db.commit()

async def get_posts(limit: int = 10):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT * FROM posts ORDER BY created DESC LIMIT ?', (limit,)) as cursor:
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) async for row in cursor]

async def add_review(user_id: int, username: str, text: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('INSERT INTO reviews (user_id, username, text) VALUES (?, ?, ?)', (user_id, username, text))
        await db.commit()

async def get_reviews(limit: int = 10):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT * FROM reviews ORDER BY created DESC LIMIT ?', (limit,)) as cursor:
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) async for row in cursor]

async def add_faq(question: str, answer: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('INSERT INTO faq (question, answer) VALUES (?, ?)', (question, answer))
        await db.commit()

async def get_faq():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT * FROM faq') as cursor:
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) async for row in cursor]

async def get_users_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT COUNT(*) FROM users') as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT tg_id, username, full_name, id as created FROM users') as cursor:
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) async for row in cursor]
