import asyncio
from add_faq_bulk import faqs
from db.db import add_faq, init_db

async def reload_faq():
    await init_db()
    for q, a in faqs:
        await add_faq(q, a)
    print('FAQ reloaded.')

if __name__ == "__main__":
    asyncio.run(reload_faq())
