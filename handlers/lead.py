from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_CHAT_ID
from handlers.antispam import can_submit_lead, update_lead_time
from handlers.main_menu import global_menu_kb
from services.export_gsheet import export_lead_to_gsheet
from db.db import add_user, add_lead
import datetime

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

from config import ADMIN_CHAT_ID
from aiogram.filters import Command

@router.message(Command("admin_test"))
async def admin_test_handler(message: types.Message):
    try:
        await message.bot.send_message(ADMIN_CHAT_ID, "Тестовое уведомление админу: всё работает!", parse_mode="HTML")
        await message.answer("Тестовое уведомление отправлено на ADMIN_CHAT_ID.")
    except Exception as e:
        await message.answer(f"Ошибка при отправке уведомления админу: {e}")


def get_fsm_nav_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="fsm_back")]
        ] + global_menu_kb.inline_keyboard
    )



class LeadForm(StatesGroup):
    name = State()
    contact = State()
    email = State()
    service = State()
    description = State()
    confirm = State()

from services.service_catalog import services

services_kb = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text=s["name"], callback_data=f"service_{i}")] for i, s in enumerate(services)])

@router.callback_query(F.data == "lead")
async def start_lead(call: types.CallbackQuery, state: FSMContext):
    print("FSM: start_lead (callback) triggered")
    await state.clear()  # Всегда очищаем состояние перед началом новой заявки
    print("[FSM] start_lead: state cleared")
    # Лимиты безопасности отключены — заявки можно отправлять без ограничений
    await add_user(
        tg_id=call.from_user.id,
        username=call.from_user.username or '',
        full_name=call.from_user.full_name or ''
    )
    await call.message.answer("Введите ваше имя:", reply_markup=get_fsm_nav_kb())
    await state.set_state(LeadForm.name)
    await call.answer()

# Новый обработчик: заказ из каталога услуги (lead_service_{idx})
@router.callback_query(F.data.startswith("lead_service_"))
async def start_lead_from_catalog(call: types.CallbackQuery, state: FSMContext):
    print("FSM: start_lead_from_catalog (callback) triggered")
    await state.clear()
    idx = int(call.data.split('_')[-1])
    from services.service_catalog import services
    service_obj = services[idx]
    await add_user(
        tg_id=call.from_user.id,
        username=call.from_user.username or '',
        full_name=call.from_user.full_name or ''
    )
    await state.update_data(service=service_obj["name"])
    await call.message.answer("Введите ваше имя:", reply_markup=get_fsm_nav_kb())
    await state.set_state(LeadForm.name)
    await call.answer()

# Новый: старт заявки по команде /lead
@router.message(Command("lead"))
async def start_lead_command(message: types.Message, state: FSMContext):
    print("FSM: start_lead (command) triggered")
    await state.clear()  # Очищаем все данные FSM
    print("[FSM] start_lead_command: state cleared")
    # Лимиты безопасности отключены — заявки можно отправлять без ограничений
    await add_user(
        tg_id=message.from_user.id,
        username=message.from_user.username or '',
        full_name=message.from_user.full_name or ''
    )
    await message.answer("Введите ваше имя:", reply_markup=get_fsm_nav_kb())
    await state.set_state(LeadForm.name)



@router.message(LeadForm.name)
async def process_name(message: types.Message, state: FSMContext):
    current = await state.get_state()
    print(f"[FSM] process_name triggered, state={current}, text={getattr(message, 'text', None)}")
    if message.text == "Назад":
        await message.answer("Вы вернулись в главное меню.", reply_markup=global_menu_kb)
        await state.clear()
        return
    if message.content_type != "text":
        await message.answer("❗️ Имя должно быть текстом. Пожалуйста, попробуйте ещё раз 😊")
        return
    await state.update_data(name=message.text)
    await message.answer("Введите ваш телефон:", reply_markup=get_fsm_nav_kb())
    await state.set_state(LeadForm.contact)
    new_state = await state.get_state()
    print(f"FSM: process_name finished, new_state={new_state}")

@router.message(LeadForm.contact)
async def lead_contact(message: types.Message, state: FSMContext):
    import re
    current = await state.get_state()
    print(f"[FSM] lead_contact triggered, state={current}, text={getattr(message, 'text', None)}")
    if message.text == "Назад":
        await message.answer("Введите ваше имя:", reply_markup=get_fsm_nav_kb())
        await state.set_state(LeadForm.name)
        return
    if message.content_type != "text":
        await message.answer("❗️ Телефон должен быть в формате +79991234567 или 89161234567. Попробуйте ещё раз!")
        return
    phone = message.text.replace(' ', '')
    if not re.fullmatch(r"^(\+7|8)[0-9]{10}$", phone):
        await message.answer("❗️ Похоже, номер телефона некорректный. Проверьте формат: +79991234567 или 89161234567.")
        return
    await state.update_data(contact=phone)
    await message.answer("Шаг 3 из 4\n✉️ Введите ваш e-mail:\n<i>На него придёт подтверждение заявки и материалы по проекту.</i>", reply_markup=get_fsm_nav_kb(), parse_mode="HTML")
    await state.set_state(LeadForm.email)
    new_state = await state.get_state()
    print(f"FSM: lead_contact finished, new_state={new_state}")

@router.message(LeadForm.email)
async def lead_email(message: types.Message, state: FSMContext):
    import re
    current = await state.get_state()
    print(f"[FSM] lead_email triggered, state={current}, text={getattr(message, 'text', None)}")
    if message.text == "Назад":
        await message.answer("Введите ваш телефон:", reply_markup=get_fsm_nav_kb())
        await state.set_state(LeadForm.contact)
        return
    if message.content_type != "text":
        await message.answer("❗️ E-mail должен быть в формате example@mail.ru. Попробуйте ещё раз!")
        return
    email = message.text.strip()
    if not re.fullmatch(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        await message.answer("❗️ Похоже, e-mail некорректный. Проверьте и попробуйте ещё раз 😊")
        return
    await state.update_data(email=email)
    data = await state.get_data()
    if data.get("service"):
        # Если услуга уже выбрана (через каталог) — сразу описание задачи
        await message.answer("Шаг 4 из 4\n📝 Опишите вашу задачу:\n<i>Расскажите, чего хотите достичь, и мы предложим лучшие AI-решения!</i>", reply_markup=get_fsm_nav_kb(), parse_mode="HTML")
        await state.set_state(LeadForm.description)
    else:
        # Если услуги нет — предложить выбрать
        await message.answer("Выберите услугу:", reply_markup=services_kb)
        await state.set_state(LeadForm.service)
    new_state = await state.get_state()
    print(f"FSM: lead_email finished, new_state={new_state}")

from services.service_catalog import services, services_list

@router.callback_query(F.data.startswith("service_"), LeadForm.service)
async def lead_service(call: types.CallbackQuery, state: FSMContext):
    import traceback
    try:
        idx = int(call.data.split('_')[1])
        service_obj = services[idx]
        await state.update_data(service=service_obj["name"])
        print(f"[FSM] lead_service: service set to {service_obj['name']}")
        desc = f"<b>{service_obj['name']}</b>\n\n{service_obj['desc']}"
        if service_obj.get('examples'):
            desc += "\n\n<b>Примеры применения:</b>"
            for ex in service_obj['examples']:
                desc += f"\n• {ex}"
        # После выбора услуги всегда просим описать задачу
        await call.message.answer(desc + "\n\n<b>Опишите вашу задачу:</b>", parse_mode="HTML", reply_markup=get_fsm_nav_kb())
        await state.set_state(LeadForm.description)
        await call.answer()
    except Exception as exc:
        tb = traceback.format_exc()
        await call.message.answer(f"❌ Ошибка при выводе услуги: {exc}\n\n<pre>{tb}</pre>", parse_mode="HTML")
        raise

@router.message(LeadForm.description)
async def process_description(message: types.Message, state: FSMContext):
    # Диагностика FSM перед подтверждением
    fsm_state_before = await state.get_state()
    print(f"[FSM-DIAG] process_description: before set_state, FSM={fsm_state_before}")
    current = await state.get_state()
    print(f"[FSM] process_description triggered, state={current}, text={getattr(message, 'text', None)}")
    if message.text == "Назад":
        await message.answer("Выберите услугу:", reply_markup=services_kb)
        await state.set_state(LeadForm.service)
        print("[FSM] process_description: user went back to service selection")
        return
    if message.content_type != "text":
        await message.answer("Пожалуйста, опишите задачу текстом.")
        return
    await state.update_data(description=message.text)
    data = await state.get_data()
    text = (
        f"Проверьте данные перед отправкой:\n"
        f"<b>Имя:</b> {data.get('name')}\n"
        f"<b>Контакт:</b> {data.get('contact')}\n"
        f"<b>Услуга:</b> {data.get('service') or '-'}\n"
        f"<b>Описание:</b> {data.get('description') or '-'}"
    )
    current2 = await state.get_state()
    if current2 == LeadForm.confirm.state:
        print('[FSM] confirm window: SKIP duplicate')
        return
    await message.answer(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отправить", callback_data="lead_confirm")],
            [InlineKeyboardButton(text="Отмена", callback_data="lead_cancel")],
            [InlineKeyboardButton(text="Назад", callback_data="fsm_back")],
        ] + global_menu_kb.inline_keyboard
    ))
    print('[FSM] confirm window sent')
    await state.set_state(LeadForm.confirm)
    fsm_state_after = await state.get_state()
    print(f"[FSM-DIAG] process_description: after set_state, FSM={fsm_state_after}")


@router.callback_query(F.data == "lead_confirm")
async def lead_confirm(call: types.CallbackQuery, state: FSMContext):
    # Диагностика FSM при нажатии кнопки
    fsm_state = await state.get_state()
    print(f"[FSM-DIAG] lead_confirm: FSM={fsm_state}, data={call.data}")
    if fsm_state != LeadForm.confirm.state:
        await call.message.answer("⚠️ Ошибка: состояние заявки сбилось. Попробуйте оформить заявку заново.", reply_markup=global_menu_kb)
        print(f"[FSM-DIAG] lead_confirm: WRONG STATE! FSM={fsm_state}, ожидалось={LeadForm.confirm.state}")
        await state.clear()
        await call.answer()
        return
    current = await state.get_state()
    print(f"[FSM] lead_confirm triggered, state={current}, data={call.data}")
    data = await state.get_data()
    print(f"[FSM] lead_confirm: FSM data before export: {data}")
    # Проверка: выбрана ли услуга
    if not data.get('service'):
        await call.message.answer("❌ Услуга не выбрана. Пожалуйста, оформите заявку заново и обязательно выберите услугу.", reply_markup=services_kb)
        await state.set_state(LeadForm.service)
        await call.answer()
        return
    # Текст для администратора
    admin_text = (
        f"Имя: {data.get('name')}\n"
        f"Контакт: {data.get('contact')}\n"
        f"E-mail: {data.get('email')}\n"
        f"Услуга: {data.get('service') or '-'}\n"
        f"Описание: {data.get('description') or '-'}"
    )
    # Сохраняем заявку в БД
    await add_lead(
        user_id=call.from_user.id,
        name=data.get('name'),
        contact=data.get('contact'),
        service=data.get('service'),
        description=data.get('description'),
        photo=None
    )
    # Экспорт в Google Sheets
    try:
        export_lead_to_gsheet(
            name=data.get('name'),
            contact=data.get('contact'),
            email=data.get('email'),
            service=data.get('service'),
            description=data.get('description')
        )
    except Exception as e:
        await call.message.answer(f"[Google Sheets] Не удалось экспортировать лид: {e}", parse_mode=None)
    # Сообщение для пользователя
    await call.message.answer("Спасибо за заявку! Менеджер свяжется с вами в ближайшее время.", reply_markup=global_menu_kb)
    # Автоматическое уведомление админу о новом лиде
    if ADMIN_CHAT_ID:
        print(f"[DEBUG] Отправка уведомления админу: {ADMIN_CHAT_ID}")
        user_full_name = call.from_user.full_name or '-'
        user_username = f"@{call.from_user.username}" if call.from_user.username else '-'
        user_id = call.from_user.id
        admin_notify = (
            "🆕 <b>Новая заявка!</b>\n"
            f"Пользователь: <b>{user_full_name}</b> ({user_username}) [id: <code>{user_id}</code>]\n"
            f"<b>Имя:</b> {data.get('name')}\n"
            f"<b>Контакт:</b> {data.get('contact')}\n"
            f"<b>Email:</b> {data.get('email')}\n"
            f"<b>Услуга:</b> {data.get('service')}\n"
            f"<b>Описание:</b> {data.get('description')}\n"
            f"<b>Дата/время:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        try:
            await call.bot.send_message(ADMIN_CHAT_ID, admin_notify, parse_mode="HTML")
            print("[DEBUG] Уведомление админу отправлено успешно!")
        except Exception as e:
            print(f"[ERROR] Ошибка при отправке уведомления админу: {e}")
            await call.message.answer(f"[Ошибка уведомления админу] {e}")
    await state.clear()
    await call.answer()

@router.callback_query(F.data == "lead_cancel", LeadForm.confirm)
async def lead_cancel(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Заявка отменена.", reply_markup=global_menu_kb)
    await state.clear()
    await call.answer()

@router.callback_query(F.data == "fsm_back")
async def fsm_back_handler(call: types.CallbackQuery, state: FSMContext):
    current = await state.get_state()
    if current == LeadForm.contact:
        await call.message.answer("Введите ваше имя:", reply_markup=get_fsm_nav_kb())
        await state.set_state(LeadForm.name)
    elif current == LeadForm.description:
        await call.message.answer("Введите ваш телефон:", reply_markup=get_fsm_nav_kb())
        await state.set_state(LeadForm.contact)
    elif current == LeadForm.confirm:
        await call.message.answer("Опишите вашу задачу", reply_markup=get_fsm_nav_kb())
        await state.set_state(LeadForm.description)
    else:
        await call.message.answer("Вы вернулись в главное меню.", reply_markup=global_menu_kb)
        await state.clear()
    await call.answer()

@router.callback_query(F.data == "fsm_main_menu")
async def fsm_main_menu_handler(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer("Вы вернулись в главное меню.", reply_markup=global_menu_kb)
    await call.answer()

@router.callback_query(F.data == "fsm_restart")
async def fsm_restart_handler(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer("Начнём заново! Введите ваше имя:", reply_markup=get_fsm_nav_kb())
    await state.set_state(LeadForm.name)
    await call.answer()
