# AURE Studio Telegram Bot

MVP Telegram-бот для AURE Studio на Python + Aiogram 3.x

## Основной функционал
- Главное меню с инлайн-кнопками
- Заявки (лидогенерация)
- Каталог услуг
- Контент-лента
- Поддержка и диалог
- Админ-панель

## Запуск
1. Установите зависимости: `pip install -r requirements.txt`
2. Запустите бота: `python bot.py`

## Структура проекта
- `bot.py` — точка входа
- `config.py` — настройки
- `handlers/` — обработчики команд и сценариев
- `db/` — работа с базой данных
- `services/` — бизнес-логика
- `admin/` — админ-команды

---

> Для запуска потребуется Telegram Bot Token (указать в .env или config.py)


## Интеграция с Google Sheets для экспорта лидов

### 1. Создайте Google Sheet для хранения лидов
- Перейдите на [Google Таблицы](https://docs.google.com/spreadsheets/u/0/) и создайте новую таблицу.
- Назовите её, например, `AI Vision Leads`.
- На первом листе (`Лист1`) создайте заголовки столбцов: `Дата`, `Имя`, `Контакт`, `Услуга`, `Описание`, `Фото`.

### 2. Создайте сервисный аккаунт Google
- Перейдите в [Google Cloud Console](https://console.cloud.google.com/).
- Создайте новый проект (если нужно).
- В меню слева выберите **APIs & Services > Credentials**.
- Нажмите **Create Credentials > Service account**.
- Дайте имя, нажмите "Создать и продолжить".
- Пропустите назначение ролей (или выберите "Editor").
- Нажмите "Готово".

### 3. Получите JSON-файл с credentials
- В списке сервисных аккаунтов нажмите на созданный аккаунт.
- Вкладка "Ключи" → "Добавить ключ" → "Создать новый ключ" (JSON).
- Скачайте файл и положите его в папку проекта, например, под именем `google-credentials.json`.

### 4. Дайте доступ сервисному аккаунту к вашей таблице
- Откройте скачанный JSON-файл, найдите поле `client_email`.
- В Google Sheets нажмите "Поделиться" и добавьте этот email с правами "Редактор".

### 5. Установите зависимости
```
pip install gspread google-auth
```

### 6. Укажите путь к credentials в .env или config.py
```
GOOGLE_CREDENTIALS_PATH=google-credentials.json
GOOGLE_SHEET_NAME=AI Vision Leads
```

### 7. Используйте пример кода для экспорта
Создайте файл `services/export_gsheet.py`:
```python
import gspread
from google.oauth2.service_account import Credentials
import os
from datetime import datetime

CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "google-credentials.json")
SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "AI Vision Leads")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
gc = gspread.authorize(creds)

sheet = gc.open(SHEET_NAME).sheet1

def export_lead_to_gsheet(name, contact, service, description, photo_url=None):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    row = [now, name, contact, service, description, photo_url or ""]
    sheet.append_row(row)
```

### 8. Вызовите экспорт из обработчика заявки
В файле `handlers/lead.py` после успешного добавления заявки:
```python
from services.export_gsheet import export_lead_to_gsheet
...
export_lead_to_gsheet(name, contact, service, description, photo_url)
```

---

**Если возникнут вопросы по настройке — напишите!**
