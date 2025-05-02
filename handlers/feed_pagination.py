from aiogram import Router, types, F
from aiogram.filters import Command
from db.db import get_posts
from handlers.main_menu import global_menu_kb

router = Router()

@router.message(Command("feed2"))
async def show_feed_paginated(message: types.Message):
    posts = await get_posts(limit=50)
    if not posts:
        await message.answer("Лента пуста.", reply_markup=global_menu_kb)
        return
    await send_feed_item(message, posts, 0)

@router.callback_query(F.data.startswith("feed_page_"))
async def paginate_feed(call: types.CallbackQuery):
    page = int(call.data.split("_")[-1])
    posts = await get_posts(limit=50)
    await send_feed_item(call.message, posts, page, edit=True, call=call)

async def send_feed_item(message, posts, page, edit=False, call=None):
    post = posts[page]
    text = post["text"] or ""
    kb = types.InlineKeyboardMarkup(inline_keyboard=[])
    if page > 0:
        kb.inline_keyboard.append([types.InlineKeyboardButton(text="⬅️ Предыдущее", callback_data=f"feed_page_{page-1}")])
    if page < len(posts) - 1:
        kb.inline_keyboard.append([types.InlineKeyboardButton(text="Следующее ➡️", callback_data=f"feed_page_{page+1}")])
    kb.inline_keyboard += global_menu_kb.inline_keyboard
    if post["photo"]:
        if edit and call:
            try:
                await call.message.edit_media(
                    types.InputMediaPhoto(media=post["photo"], caption=text, parse_mode="HTML"),
                    reply_markup=kb
                )
            except Exception:
                await call.message.edit_caption(
                    caption=text,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            await call.answer()
        else:
            await message.answer_photo(post["photo"], caption=text, reply_markup=kb, parse_mode="HTML")
    else:
        if edit and call:
            await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
            await call.answer()
        else:
            await message.answer(text, reply_markup=kb, parse_mode="HTML")
