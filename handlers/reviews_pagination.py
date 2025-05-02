from aiogram import Router, types, F
from aiogram.filters import Command
from db.db import get_reviews
from handlers.main_menu import global_menu_kb

router = Router()

@router.message(Command("reviews2"))
async def show_reviews_paginated(message: types.Message):
    reviews = await get_reviews(limit=50)
    if not reviews:
        await message.answer("Пока нет отзывов.", reply_markup=global_menu_kb)
        return
    await send_review_item(message, reviews, 0)

@router.callback_query(F.data.startswith("review_page_"))
async def paginate_reviews(call: types.CallbackQuery):
    page = int(call.data.split("_")[-1])
    reviews = await get_reviews(limit=50)
    await send_review_item(call.message, reviews, page, edit=True, call=call)

async def send_review_item(message, reviews, page, edit=False, call=None):
    r = reviews[page]
    user = r["username"] or "Пользователь"
    text = f"<b>{user}:</b> {r['text']}"
    kb = types.InlineKeyboardMarkup(inline_keyboard=[])
    if page > 0:
        kb.inline_keyboard.append([types.InlineKeyboardButton(text="⬅️ Предыдущее", callback_data=f"review_page_{page-1}")])
    if page < len(reviews) - 1:
        kb.inline_keyboard.append([types.InlineKeyboardButton(text="Следующее ➡️", callback_data=f"review_page_{page+1}")])
    kb.inline_keyboard += global_menu_kb.inline_keyboard
    if edit and call:
        try:
            await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            pass
        await call.answer()
    else:
        await message.answer(text, reply_markup=kb, parse_mode="HTML")
