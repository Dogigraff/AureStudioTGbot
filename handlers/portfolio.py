from aiogram import Router, types, F
from aiogram.filters import Command
from config import ADMIN_CHAT_ID
from db.portfolio import add_portfolio_item, get_portfolio
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from handlers.main_menu import global_menu_kb
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

from aiogram import types, F

@router.callback_query(F.data == "portfolio")
async def show_portfolio_callback(call: types.CallbackQuery):
    await show_portfolio(call.message)
    await call.answer()

def get_fsm_nav_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="fsm_back")],
        ] + global_menu_kb.inline_keyboard
    )

class PortfolioFSM(StatesGroup):
    waiting_for_title = State()
    waiting_for_desc = State()
    waiting_for_photo = State()

@router.message(Command("add_portfolio"))
async def add_portfolio_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    await message.answer("Введите название работы для портфолио:", reply_markup=get_fsm_nav_kb())
    await state.set_state(PortfolioFSM.waiting_for_title)

@router.message(PortfolioFSM.waiting_for_title)
async def add_portfolio_title(message: types.Message, state: FSMContext):
    print(f"FSM: add_portfolio_title triggered, text={getattr(message, 'text', None)}, type={message.content_type}")
    if message.text == "Назад":
        await message.answer("Выход в главное меню.", reply_markup=global_menu_kb)
        await state.clear()
        return
    if message.content_type != "text":
        await message.answer("Пожалуйста, введите название работы текстом.")
        return
    await state.update_data(title=message.text)
    await message.answer("Введите описание работы (или - если не нужно):", reply_markup=get_fsm_nav_kb())
    await state.set_state(PortfolioFSM.waiting_for_desc)

@router.message(PortfolioFSM.waiting_for_desc)
async def add_portfolio_desc(message: types.Message, state: FSMContext):
    print(f"FSM: add_portfolio_desc triggered, text={getattr(message, 'text', None)}, type={message.content_type}")
    if message.text == "Назад":
        await message.answer("Введите название работы для портфолио:", reply_markup=get_fsm_nav_kb())
        await state.set_state(PortfolioFSM.waiting_for_title)
        return
    if message.content_type != "text":
        await message.answer("Пожалуйста, введите описание работы текстом.")
        return
    await state.update_data(description=message.text)
    await message.answer("Прикрепите фото работы:", reply_markup=get_fsm_nav_kb())
    await state.set_state(PortfolioFSM.waiting_for_photo)

@router.message(PortfolioFSM.waiting_for_photo)
async def add_portfolio_photo(message: types.Message, state: FSMContext):
    print(f"FSM: add_portfolio_photo triggered, type={message.content_type}")
    if message.text == "Назад":
        await message.answer("Введите описание работы (или - если не нужно):", reply_markup=get_fsm_nav_kb())
        await state.set_state(PortfolioFSM.waiting_for_desc)
        return
    if not message.photo:
        await message.answer("Пожалуйста, отправьте фото работы.", reply_markup=get_fsm_nav_kb())
        return
    data = await state.get_data()
    photo = message.photo[-1].file_id
    await add_portfolio_item(
        author_id=message.from_user.id,
        title=data.get("title"),
        description=data.get("description"),
        photo=photo
    )
    await message.answer("Работа добавлена в портфолио!", reply_markup=global_menu_kb)
    await state.clear()

@router.message(Command("portfolio"))
async def show_portfolio(message: types.Message):
    items = await get_portfolio(limit=10)
    if not items:
        await message.answer("Портфолио пока пусто. Посмотреть примеры работ можно на https://www.aurestudio.ru/", reply_markup=global_menu_kb)
        return
    for idx, item in enumerate(items[::-1]):
        text = f"<b>{item['title']}</b>\n{item['description'] or ''}"
        if idx == len(items) - 1:
            text += "\n\nБольше работ — на сайте: https://www.aurestudio.ru/"
            await message.answer_photo(item["photo"], caption=text, reply_markup=global_menu_kb)
        else:
            await message.answer_photo(item["photo"], caption=text)

@router.callback_query(F.data == "fsm_back")
async def fsm_back_portfolio(call: types.CallbackQuery, state: FSMContext):
    current = await state.get_state()
    if current == PortfolioFSM.waiting_for_desc:
        await call.message.answer("Введите название работы для портфолио:", reply_markup=get_fsm_nav_kb())
        await state.set_state(PortfolioFSM.waiting_for_title)
    elif current == PortfolioFSM.waiting_for_photo:
        await call.message.answer("Введите описание работы (или - если не нужно):", reply_markup=get_fsm_nav_kb())
        await state.set_state(PortfolioFSM.waiting_for_desc)
    else:
        await call.message.answer("Выход в главное меню.", reply_markup=global_menu_kb)
        await state.clear()
    await call.answer()
