from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db.db import add_review, get_reviews, add_faq, get_faq
from config import ADMIN_CHAT_ID
from handlers.main_menu import global_menu_kb
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from services.export_gsheet_reviews import export_review_to_gsheet

router = Router()

from aiogram import types, F

@router.callback_query(F.data == "reviews")
async def show_reviews_callback(call: types.CallbackQuery):
    await show_reviews(call.message)
    await call.answer()

def get_fsm_nav_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="fsm_back")],
        ] + global_menu_kb.inline_keyboard
    )

# --- Отзывы ---
class ReviewFSM(StatesGroup):
    waiting_for_review = State()

@router.message(Command("review"))
async def start_review(message: types.Message, state: FSMContext):
    await message.answer("Пожалуйста, напишите ваш отзыв:", reply_markup=get_fsm_nav_kb())
    await state.set_state(ReviewFSM.waiting_for_review)

@router.message(ReviewFSM.waiting_for_review)
async def save_review(message: types.Message, state: FSMContext):
    print(f"FSM: save_review triggered, text={getattr(message, 'text', None)}, type={message.content_type}")
    if message.text == "Назад":
        await message.answer("Выход в главное меню.", reply_markup=global_menu_kb)
        await state.clear()
        return
    if message.content_type != "text":
        await message.answer("Пожалуйста, напишите отзыв текстом.")
        return
    await add_review(message.from_user.id, message.from_user.username or '', message.text)
    # Экспорт в Google Sheets
    try:
        export_review_to_gsheet(
            username=message.from_user.username or '',
            user_id=message.from_user.id,
            review_text=message.text
        )
    except Exception as e:
        await message.answer(f"[Google Sheets] Не удалось экспортировать отзыв: {e}")
    await message.answer("Спасибо за ваш отзыв! Больше отзывов — на https://www.aurestudio.ru/", reply_markup=global_menu_kb)
    await state.clear()

@router.message(Command("reviews"))
async def show_reviews(message: types.Message):
    reviews = await get_reviews(limit=10)
    if not reviews:
        await message.answer("Пока нет отзывов.", reply_markup=global_menu_kb)
        return
    text = "<b>Отзывы клиентов:</b>\n\nБольше отзывов — на https://www.aurestudio.ru/\n"
    for idx, r in enumerate(reviews[::-1]):
        user = r["username"] or "Пользователь"
        text += f"\n<b>{user}:</b> {r['text']}"
        if idx == len(reviews) - 1:
            await message.answer(text, reply_markup=global_menu_kb)
        else:
            await message.answer(text)

# --- FAQ ---
class FAQFSM(StatesGroup):
    waiting_for_question = State()
    waiting_for_answer = State()

@router.message(Command("add_faq"))
async def add_faq_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    await message.answer("Введите вопрос для FAQ:", reply_markup=get_fsm_nav_kb())
    await state.set_state(FAQFSM.waiting_for_question)

@router.message(FAQFSM.waiting_for_question)
async def add_faq_question(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await message.answer("Выход в главное меню.", reply_markup=global_menu_kb)
        await state.clear()
        return
    await state.update_data(question=message.text)
    await message.answer("Введите ответ на вопрос:", reply_markup=get_fsm_nav_kb())
    await state.set_state(FAQFSM.waiting_for_answer)

@router.message(FAQFSM.waiting_for_answer)
async def add_faq_answer(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await message.answer("Введите вопрос для FAQ:", reply_markup=get_fsm_nav_kb())
        await state.set_state(FAQFSM.waiting_for_question)
        return
    data = await state.get_data()
    await add_faq(data["question"], message.text)
    await message.answer("FAQ добавлен!", reply_markup=global_menu_kb)
    await state.clear()

@router.message(Command("faq"))
async def show_faq(message: types.Message):
    await show_faq_core(message)

@router.callback_query(F.data == "faq")
async def show_faq_callback(callback: types.CallbackQuery):
    await show_faq_core(callback.message)
    await callback.answer()

async def show_faq_core(message):
    faq = await get_faq()
    if not faq:
        await message.answer("FAQ пока пуст.", reply_markup=global_menu_kb)
        return
    # Формируем инлайн-кнопки по вопросам
    buttons = [
        [InlineKeyboardButton(text=q['question'].replace('AI Vision Studio', 'AURE Studio')[:64], callback_data=f"faq_{q['id']}")]
        for q in faq
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons + global_menu_kb.inline_keyboard)
    await message.answer("<b>Выберите интересующий вопрос:</b>", reply_markup=kb)

@router.callback_query(F.data.startswith("faq_"))
async def show_faq_answer(callback: types.CallbackQuery):
    faq = await get_faq()
    qid = int(callback.data.replace("faq_", ""))
    item = next((q for q in faq if q['id'] == qid), None)
    if item:
        q = item['question'].replace('AI Vision Studio', 'AURE Studio')
        a = item['answer'].replace('AI Vision Studio', 'AURE Studio')
        text = f"<b>Q:</b> {q}\n<b>A:</b> {a}"
        await callback.message.answer(text, reply_markup=global_menu_kb)
    else:
        await callback.message.answer("Вопрос не найден.", reply_markup=global_menu_kb)
    await callback.answer()
