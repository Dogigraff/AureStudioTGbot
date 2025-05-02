from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_CHAT_ID
from handlers.main_menu import global_menu_kb

router = Router()

# FSM для live chat (от пользователя)
class LiveChatFSM(StatesGroup):
    waiting_for_message = State()
    waiting_for_reply = State()

# Пользователь инициирует диалог с оператором
@router.message(Command("operator"))
async def call_operator(message: types.Message, state: FSMContext):
    await message.answer("Напишите ваше сообщение для оператора:")
    await state.set_state(LiveChatFSM.waiting_for_message)

@router.message(LiveChatFSM.waiting_for_message)
async def forward_to_admin(message: types.Message, state: FSMContext):
    # Пересылаем сообщение админу
    await message.bot.send_message(
        ADMIN_CHAT_ID,
        f"<b>Live Chat:</b>\nОт: {message.from_user.full_name} (@{message.from_user.username}) [id: {message.from_user.id}]\n\n{message.text}",
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[[types.InlineKeyboardButton(text="Ответить", callback_data=f"reply_{message.from_user.id}")]]
        )
    )
    await message.answer("Ваше сообщение отправлено оператору. Ожидайте ответ.", reply_markup=global_menu_kb)
    await state.clear()

# Админ нажимает "Ответить" — FSM для ответа
@router.callback_query(F.data.startswith("reply_"))
async def admin_reply_callback(call: types.CallbackQuery, state: FSMContext):
    user_id = int(call.data.split("_")[1])
    await state.update_data(reply_user_id=user_id)
    await call.message.answer(f"Введите ответ для пользователя [id: {user_id}]:")
    await state.set_state(LiveChatFSM.waiting_for_reply)
    await call.answer()

@router.message(LiveChatFSM.waiting_for_reply)
async def send_admin_reply(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("reply_user_id")
    if not user_id:
        await message.answer("Ошибка: не найден пользователь для ответа.", reply_markup=global_menu_kb)
        await state.clear()
        return
    try:
        await message.bot.send_message(user_id, f"Оператор: {message.text}")
        await message.answer("Ответ отправлен пользователю.", reply_markup=global_menu_kb)
    except Exception:
        await message.answer("Не удалось отправить сообщение пользователю.", reply_markup=global_menu_kb)
    await state.clear()
