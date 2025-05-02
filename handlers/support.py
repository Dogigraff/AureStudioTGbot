from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_CHAT_ID

router = Router()

@router.callback_query(F.data == "support")
async def support_request(call: types.CallbackQuery):
    await call.message.answer("Оператор свяжется с вами в ближайшее время.")
    if ADMIN_CHAT_ID:
        await call.bot.send_message(ADMIN_CHAT_ID, f"Пользователь {call.from_user.full_name} (@{call.from_user.username}) просит связаться.")
    await call.answer()
