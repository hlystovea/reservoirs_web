import asyncio
import logging
from logging.handlers import RotatingFileHandler
from os import environ

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import BotCommand

from bot.handlers.common import register_common_handlers
from bot.handlers.water_situation import register_water_situation_handlers

BOT_TOKEN = environ.get('BOT_BWU')


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(funcName)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler('logs/bot.log', 5000000, 2)
    ],
)


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(bot, storage=MemoryStorage())

    commands = [
        BotCommand(command='/start', description='начать'),
        BotCommand(command='/help', description='помощь'),
        BotCommand(command='/menu', description='открыть меню')
    ]
    await bot.set_my_commands(commands)

    register_common_handlers(dp)
    register_water_situation_handlers(dp)

    await dp.start_polling()


if __name__ == '__main__':
    asyncio.run(main())
