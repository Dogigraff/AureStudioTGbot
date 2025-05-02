from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

router = Router()

from services.service_catalog import services, services_list
from handlers.main_menu import global_menu_kb

catalog_kb = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text=s["name"], callback_data=f"svc_{i}")] for i, s in enumerate(services)])

@router.callback_query(F.data == "services")
async def show_catalog(call: types.CallbackQuery):
    await call.message.answer("Каталог услуг:")
    kb = InlineKeyboardMarkup(
        inline_keyboard=catalog_kb.inline_keyboard + global_menu_kb.inline_keyboard
    )
    await call.message.answer("Каталог услуг:", reply_markup=kb)
    await call.answer()

@router.callback_query(F.data.startswith("svc_"))
async def show_service_card(call: types.CallbackQuery):
    idx = int(call.data.split('_')[1])
    svc = services[idx]
    # Кнопка 'Заказать' вызывает callback_data='lead', обработчик находится в lead.py
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Заказать", callback_data=f"lead_service_{idx}")],
        [InlineKeyboardButton(text="Назад", callback_data="services")],
    ] + global_menu_kb.inline_keyboard)
    desc = f"<b>{svc['name']}</b>\n{svc['desc']}"
    if svc.get('examples'):
        desc += "\n\n<b>Примеры применения:</b>"
        for ex in svc['examples']:
            desc += f"\n• {ex}"
    await call.message.answer(desc, reply_markup=kb, parse_mode="HTML")
    await call.answer()
