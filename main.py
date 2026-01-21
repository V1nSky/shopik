import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database.models import init_db
from handlers import user, admin

# -------------------- ЛОГИРОВАНИЕ --------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# -------------------- MAIN --------------------
async def main():
    """Главная функция запуска бота"""

    # Инициализация бота (aiogram 3.7+)
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Диспетчер
    dp = Dispatcher()

    # Инициализация базы данных
    init_db()
    logger.info("База данных инициализирована")

    # Подключение роутеров
    dp.include_router(user.router)
    dp.include_router(admin.router)

    logger.info("Бот запущен")

    # Запуск polling
    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types()
    )


# -------------------- ENTRY POINT --------------------
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
