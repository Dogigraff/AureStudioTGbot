from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_CHAT_ID
from db.db import get_all_subscribed_users, set_user_subscribed, add_user, add_post, get_posts
from handlers.main_menu import global_menu_kb

router = Router()

@router.message(Command("post"))
async def post_content(message: types.Message):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    await message.answer("Отправьте текст или фото для публикации:")

@router.message(F.reply_to_message, F.from_user.id == ADMIN_CHAT_ID)
async def publish_content(message: types.Message):
    # Сохраняем публикацию в БД
    photo = message.photo[-1].file_id if message.photo else None
    await add_post(author_id=message.from_user.id, text=message.text or message.caption, photo=photo)
    user_ids = await get_all_subscribed_users()
    for user_id in user_ids:
        try:
            if message.photo:
                await message.bot.send_photo(user_id, photo, caption=message.caption or message.text or "")
            else:
                await message.bot.send_message(user_id, message.text or "")
        except Exception:
            pass
    await message.answer("Контент отправлен подписчикам и сохранён в ленте.", reply_markup=global_menu_kb)

@router.message(Command("feed"))
async def show_feed(message: types.Message):
    posts = await get_posts(limit=5)
    if not posts:
        await message.answer("Лента пуста.", reply_markup=global_menu_kb)
        return
    for post in posts[::-1]:  # Показать от старых к новым
        if post["photo"]:
            await message.answer_photo(post["photo"], caption=post["text"] or "")
        else:
            await message.answer(post["text"] or "[Без текста]")
    await message.answer("Конец ленты.", reply_markup=global_menu_kb)

@router.message(Command("subscribe"))
async def subscribe(message: types.Message):
    # Сохраняем пользователя и отмечаем подписку
    await add_user(
        tg_id=message.from_user.id,
        username=message.from_user.username or '',
        full_name=message.from_user.full_name or ''
    )
    await set_user_subscribed(message.from_user.id, 1)
    await message.answer("Вы подписались на новости!")

@router.message(Command("unsubscribe"))
async def unsubscribe(message: types.Message):
    await set_user_subscribed(message.from_user.id, 0)
    await message.answer("Вы отписались от новостей.")
