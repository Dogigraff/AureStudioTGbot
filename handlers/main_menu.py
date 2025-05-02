from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

@router.callback_query(F.data == "main_menu")
async def main_menu_callback(call: types.CallbackQuery):
    await call.message.answer("Главное меню открыто.", reply_markup=main_menu_kb)
    await call.answer()

main_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Услуги и примеры", callback_data="services")],
    [InlineKeyboardButton(text="Оставить заявку", callback_data="lead")],
    [InlineKeyboardButton(text="Портфолио", callback_data="portfolio")],
    [InlineKeyboardButton(text="Отзывы", callback_data="reviews")],
    [InlineKeyboardButton(text="FAQ", callback_data="faq")],
    [InlineKeyboardButton(text="Связаться с оператором", callback_data="support")],
])

global_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
    ]
)

@router.message(Command("start", "help"))
async def cmd_start(message: types.Message):
    user_name = message.from_user.full_name or message.from_user.username or "гость"
    text = (
        f"✨ <b>Добро пожаловать в AURE Studio, {user_name}!</b>\n\n"
        "Создаём AI-видео, цифровых аватаров, нейрофотосессии и Telegram-ботов для брендов и креаторов.\n\n"
        "<b>Что я могу для вас сделать:</b>\n"
        "🪄 Услуги и примеры\n"
        "📝 Оставить заявку\n"
        "💼 Портфолио\n"
        "💬 Отзывы\n"
        "🤖 FAQ\n"
        "👤 Связаться с оператором\n\n"
        "<i>На каждом этапе заявки теперь доступны кнопки: 'Назад', 'Главное меню', 'Заполнить заново'.\nВыберите нужный раздел с помощью кнопок ниже:</i>"
    )
    await message.answer(
        text,
        reply_markup=main_menu_kb,
        parse_mode="HTML"
    )
