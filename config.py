import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = 228528450
DATABASE_URL = os.getenv("DATABASE_URL", "ai_vision_studio.db")
