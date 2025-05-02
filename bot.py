import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from aiogram.filters import Command
from config import BOT_TOKEN
from handlers import main_menu, lead, catalog, support, admin, content
from handlers import portfolio
from handlers import reviews_faq
from handlers import livechat
from handlers import portfolio_pagination
from handlers import reviews_pagination
from handlers import feed_pagination
from db.db import init_db

async def main():
    logging.basicConfig(level=logging.INFO)
    await init_db()
    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрация роутеров
    dp.include_router(main_menu.router)
    dp.include_router(lead.router)
    dp.include_router(catalog.router)
    dp.include_router(content.router)
    dp.include_router(support.router)
    dp.include_router(admin.router)
    dp.include_router(portfolio.router)
    # reviews_faq.router теперь регистрируется ДО livechat и других общих роутеров
    dp.include_router(reviews_faq.router)
    # Далее идут роутеры, которые могут ловить любые текстовые сообщения
    dp.include_router(livechat.router)
    dp.include_router(portfolio_pagination.router)
    dp.include_router(reviews_pagination.router)
    dp.include_router(feed_pagination.router)

    # Команды для меню
    await bot.set_my_commands([
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="help", description="Помощь"),
        BotCommand(command="faq", description="Частые вопросы")
    ])

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
