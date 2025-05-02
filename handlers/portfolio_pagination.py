from aiogram import Router, types, F
from aiogram.filters import Command
from db.portfolio import get_portfolio
from handlers.main_menu import global_menu_kb

router = Router()

@router.message(Command("portfolio2"))
async def show_portfolio_paginated(message: types.Message):
    items = await get_portfolio(limit=20)
    if not items:
        await message.answer("Портфолио пока пусто.", reply_markup=global_menu_kb)
        return
    await send_portfolio_item(message, items, 0)

@router.callback_query(F.data.startswith("portfolio_page_"))
async def paginate_portfolio(call: types.CallbackQuery):
    page = int(call.data.split("_")[-1])
    items = await get_portfolio(limit=20)
    await send_portfolio_item(call.message, items, page, edit=True, call=call)

async def send_portfolio_item(message, items, page, edit=False, call=None):
    item = items[page]
    text = f"<b>{item['title']}</b>\n{item['description'] or ''}"
    kb = types.InlineKeyboardMarkup(inline_keyboard=[])
    if page > 0:
        kb.inline_keyboard.append([types.InlineKeyboardButton(text="⬅️ Предыдущее", callback_data=f"portfolio_page_{page-1}")])
    if page < len(items) - 1:
        kb.inline_keyboard.append([types.InlineKeyboardButton(text="Следующее ➡️", callback_data=f"portfolio_page_{page+1}")])
    kb.inline_keyboard += global_menu_kb.inline_keyboard
    if edit and call:
        try:
            await call.message.edit_media(
                types.InputMediaPhoto(media=item["photo"], caption=text, parse_mode="HTML"),
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
        await message.answer_photo(item["photo"], caption=text, reply_markup=kb, parse_mode="HTML")
