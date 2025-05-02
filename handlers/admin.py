from aiogram import Router, types, F
from aiogram.filters import Command
from config import ADMIN_CHAT_ID
from db.db import get_users_count, get_leads, get_all_users, mark_lead_notified, get_new_leads
from db.db import get_unprocessed_leads_for_reminder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.service_catalog import services
from services.export_gsheet import export_lead_to_gsheet
import aiosqlite
import importlib

router = Router()

class MailingFSM(StatesGroup):
    waiting_for_content = State()

@router.message(Command("mailing"))
async def mailing(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    await message.answer("Введите текст или фото для рассылки всем подписчикам:")
    await state.set_state(MailingFSM.waiting_for_content)

@router.message(MailingFSM.waiting_for_content)
async def do_mailing(message: types.Message, state: FSMContext):
    from db.db import get_all_subscribed_users
    user_ids = await get_all_subscribed_users()
    sent = 0
    for user_id in user_ids:
        try:
            if message.photo:
                photo = message.photo[-1].file_id
                await message.bot.send_photo(user_id, photo, caption=message.caption or message.text or "")
            else:
                await message.bot.send_message(user_id, message.text or "")
            sent += 1
        except Exception:
            pass
    await message.answer(f"Рассылка завершена! Доставлено: {sent} из {len(user_ids)}")
    await state.clear()

@router.message(Command("users"))
async def users_count(message: types.Message):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    count = await get_users_count()
    await message.answer(f"Количество пользователей: <b>{count}</b>")

@router.message(Command("lastleads"))
async def last_leads(message: types.Message):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    leads = await get_leads()
    if not leads:
        await message.answer("Заявок пока нет.")
        return
    text = "<b>Последние заявки:</b>\n"
    for lead in leads[:10]:
        text += (
            f"\n<b>ID:</b> {lead['id']}"
            f"\n<b>Имя:</b> {lead['name']}"
            f"\n<b>Контакт:</b> {lead['contact']}"
            f"\n<b>E-mail:</b> {lead.get('email','-')}"
            f"\n<b>Услуга:</b> {lead.get('service','-')}"
            f"\n<b>Описание:</b> {lead.get('description','-')}"
            f"\n<b>Дата:</b> {lead['created']}"
            f"\n<b>Статус:</b> {lead.get('status','-')}"
            f"\n<b>Notified:</b> {lead.get('notified','-')}"
            "\n---"
        )
    await message.answer(text)

@router.message(Command("lead_done"))
async def lead_done(message: types.Message):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Используйте: /lead_done <id>")
        return
    lead_id = int(parts[1])
    # Обновляем статус и notified
    from db.db import aiosqlite, DB_PATH
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE leads SET status='обработана', notified=1 WHERE id=?", (lead_id,))
        await db.commit()
    await message.answer(f"Заявка {lead_id} отмечена как обработанная.")

class EditServiceFSM(StatesGroup):
    waiting_for_service = State()
    waiting_for_desc = State()

@router.message(Command("export_new_leads_gsheet"))
async def export_new_leads_gsheet(message: types.Message):
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    await message.answer("Начинаю экспорт новых заявок в Google Sheets...")
    try:
        if message.from_user.id != ADMIN_CHAT_ID:
            await message.answer("Нет доступа. Только для администратора.")
            return
        leads = await get_new_leads()
        if not leads:
            await message.answer("Нет новых заявок для экспорта.")
            return
        exported = 0
        errors = []
        loop = asyncio.get_running_loop()
        executor = ThreadPoolExecutor()
        for lead in leads:
            try:
                await loop.run_in_executor(executor, export_lead_to_gsheet,
                    lead.get('name'),
                    lead.get('contact'),
                    lead.get('service'),
                    lead.get('description'),
                    lead.get('photo')
                )
                # После успешного экспорта меняем статус
                async with aiosqlite.connect('ai_vision_studio.db') as db:
                    await db.execute("UPDATE leads SET status='экспортирована' WHERE id=?", (lead['id'],))
                    await db.commit()
                exported += 1
            except Exception as e:
                errors.append(f"ID {lead['id']}: {e}")
        await message.answer(f"Экспорт завершён. Экспортировано заявок: {exported} из {len(leads)}")
        if errors:
            await message.answer("Ошибки:\n" + "\n".join(errors))
    except Exception as exc:
        await message.answer(f"❌ Ошибка при выполнении экспорта: {exc}")
        import traceback
        tb = traceback.format_exc()
        await message.answer(f"Traceback:\n{tb}")


@router.message(Command("export_leads"))
async def export_leads(message: types.Message):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    path = await export_leads_to_csv()
    if not path:
        await message.answer("Нет заявок для экспорта.")
        return
    await message.answer_document(types.FSInputFile(path), caption="Экспорт заявок (CSV)")

@router.message(Command("export_reviews"))
async def export_reviews(message: types.Message):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    path = await export_reviews_to_csv()
    if not path:
        await message.answer("Нет отзывов для экспорта.")
        return
    await message.answer_document(types.FSInputFile(path), caption="Экспорт отзывов (CSV)")

@router.message(Command("export_users"))
async def export_users(message: types.Message):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    path = await export_users_to_csv(get_all_users)
    if not path:
        await message.answer("Нет пользователей для экспорта.")
        return
    await message.answer_document(types.FSInputFile(path), caption="Экспорт пользователей (CSV)")

@router.message(Command("test_gsheet"))
async def test_gsheet(message: types.Message):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    try:
        export_lead_to_gsheet(
            name="Test User",
            contact="+79991234567",
            service="Test Service",
            description="This is a test entry from /test_gsheet command.",
            photo_url=None
        )
        export_review_to_gsheet(
            username="test_admin",
            user_id=message.from_user.id,
            review_text="Test review from /test_gsheet command."
        )
        await message.answer("✅ Google Sheets интеграция работает: тестовые данные успешно записаны.")
    except Exception as e:
        await message.answer(f"❌ Ошибка интеграции с Google Sheets: {e}")

@router.message(Command("edit_services"))
async def edit_services(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    kb = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text=s["name"])] for s in services],
        resize_keyboard=True, one_time_keyboard=True
    )
    await message.answer("Выберите услугу для редактирования:", reply_markup=kb)
    await state.set_state(EditServiceFSM.waiting_for_service)

@router.message(EditServiceFSM.waiting_for_service)
async def choose_service(message: types.Message, state: FSMContext):
    names = [s["name"] for s in services]
    if message.text not in names:
        await message.answer("Пожалуйста, выберите услугу из списка.")
        return
    await state.update_data(service_name=message.text)
    await message.answer(f"Введите новое описание для услуги \"{message.text}\":", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(EditServiceFSM.waiting_for_desc)

@router.message(EditServiceFSM.waiting_for_desc)
async def set_new_desc(message: types.Message, state: FSMContext):
    data = await state.get_data()
    service_name = data.get("service_name")
    # Обновляем описание в services
    for s in services:
        if s["name"] == service_name:
            s["desc"] = message.text
            break
    # Сохраняем изменения в файле
    from services import service_catalog
    importlib.reload(service_catalog)
    with open(service_catalog.__file__, "r", encoding="utf-8") as f:
        lines = f.readlines()
    # Примитивное обновление по ключу desc
    with open(service_catalog.__file__, "w", encoding="utf-8") as f:
        for line in lines:
            if f'"name": "{service_name}"' in line:
                f.write(line)
                nextline = next(lines)
                f.write(f'        "desc": "{message.text}",\n')
            else:
                f.write(line)
    await message.answer(f"Описание услуги \"{service_name}\" обновлено!", reply_markup=types.ReplyKeyboardRemove())
    await state.clear()
