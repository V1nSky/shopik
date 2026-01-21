import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ID администратора
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Токен ЮKassa
YUKASSA_TOKEN = os.getenv("YUKASSA_TOKEN")
YUKASSA_SHOP_ID = os.getenv("YUKASSA_SHOP_ID")

# База данных
DATABASE_PATH = os.getenv("DATABASE_PATH", "shop.db")

# Проверка наличия обязательных переменных
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен в .env файле")
if not ADMIN_ID:
    raise ValueError("ADMIN_ID не установлен в .env файле")
if not YUKASSA_TOKEN:
    raise ValueError("YUKASSA_TOKEN не установлен в .env файле")
if not YUKASSA_SHOP_ID:
    raise ValueError("YUKASSA_SHOP_ID не установлен в .env файле")