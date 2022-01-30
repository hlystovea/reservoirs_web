import asyncio
import logging
from logging.handlers import RotatingFileHandler
from os import environ

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import BotCommand

from bot.handlers.common import register_common_handlers
from bot.handlers.water_situation import register_water_situation_handlers
from db.postgres import db

BOT_TOKEN = environ.get('BOT_BWU')
DATABASE_URL = environ.get('DATABASE_URL')


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(funcName)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler('logs/bot.log', 5000000, 2)
    ],
)


commands = [
    BotCommand(command='/start', description='- начать'),
    BotCommand(command='/help', description='- помощь'),
    BotCommand(command='/menu', description='- открыть меню')
]


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


async def main():
    await bot.set_my_commands(commands)

    register_common_handlers(dp)
    register_water_situation_handlers(dp)

    await dp.start_polling()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(db.setup())
        loop.run_until_complete(main())
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        db.stop()
        loop.close()
