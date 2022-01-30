import asyncio
import datetime as dt
import logging
from logging.handlers import RotatingFileHandler
from os import environ
from typing import Dict, List, Tuple, Union

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData
from dateutil.parser import parse, ParserError

from core.db.schemas import Region, Reservoir
from core.db.postgres import PostgresDB
from core.utils.plotter import plotter

BOT_TOKEN = environ.get('BOT_BWU')
DATABASE_URL = environ.get('DATABASE_URL')


class NoDataError(Exception):
    pass


console_out_hundler = logging.StreamHandler()
rotate_file_handler = RotatingFileHandler(
    'log.log',
    maxBytes=5000000,
    backupCount=2,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(funcName)s: %(message)s',
    handlers=[console_out_hundler, rotate_file_handler],
)


class TgBot(Bot):
    def __init__(self, token, db):
        self.db = db
        super().__init__(token)


db = PostgresDB(DATABASE_URL)
storage = MemoryStorage()
bot = TgBot(token=BOT_TOKEN, db=db)
dp = Dispatcher(bot, storage=storage)

main_cb = CallbackData('main', 'action', 'answer')

time_buttons = {
    7: 'Неделя',
    30: 'Месяц',
    183: 'Пол года',
    365: 'Год',
    10000: 'За всё время',
    'manually': 'Ввести даты вручную',
}

command_buttons = {
    'level': 'Построить график УВБ',
    'inflow': 'Построить график притока',
    'outflow': 'Построить график сброса',
    'spillway': 'Построить график холостых сбросов',
}


class MainState(StatesGroup):
    waiting_for_region = State()
    waiting_for_reservoir = State()
    waiting_for_command = State()
    waiting_for_period = State()
    waiting_for_date1 = State()
    waiting_for_date2 = State()


def get_markup_with_objs(action: str, objs: List[Union[Reservoir, Region]]):
    markup = types.InlineKeyboardMarkup()
    for obj in objs:
        button = types.InlineKeyboardButton(
            obj.name, callback_data=main_cb.new(action=action, answer=obj.slug)
        )
        markup.add(button)
    return markup


def get_markup_with_items(action: str, items: Dict):
    markup = types.InlineKeyboardMarkup()
    for key, value in items.items():
        button = types.InlineKeyboardButton(
            value, callback_data=main_cb.new(action=action, answer=key)
        )
        markup.add(button)
    return markup


@dp.message_handler(commands=['start', 'help'], state='*')
async def start(message: types.Message, state: FSMContext):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await state.finish()
    text = (
        'Привет! Я бот, который по данным [сайта РусГидро]'
        '(http://www.rushydro.ru/hydrology/informer) строит графики '
        'гидрологического режима водохранилищ ГЭС России. '
        'Чтобы начать, нажмите *"Выбрать водохранилище"*'
    )
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Выбрать водохранилище')
    await message.answer(
        text,
        reply_markup=markup,
        parse_mode='Markdown',
        disable_notification=True,
    )


@dp.message_handler(text=['Выбрать водохранилище'], state='*')
async def start_message_handler(message: types.Message, state: FSMContext):
    """
    This handler will be called when user sends text "Выбрать водохранилище"
    """
    await state.finish()
    regions = await bot.db.get_all_regions()
    markup = get_markup_with_objs(action='region', objs=regions)
    await message.answer(
        text='Выберите регион:',
        reply_markup=markup,
        disable_notification=True,
        disable_web_page_preview=True,
    )
    await message.delete()
    await MainState.waiting_for_region.set()


@dp.callback_query_handler(main_cb.filter(action='start'), state='*')
async def back_to_list_regions(
    query: types.CallbackQuery,
    callback_data: Dict[str, str],
    state: FSMContext,
):
    """
    This handler will be called when the user sends
    query with "start" action
    """
    await state.finish()
    regions = await bot.db.get_all_regions()
    markup = get_markup_with_objs(action='region', objs=regions)
    await query.message.edit_text(
        text='Выберите регион:', reply_markup=markup
    )
    await MainState.waiting_for_region.set()


@dp.callback_query_handler(
    main_cb.filter(action='region'),
    state=[MainState.waiting_for_region, MainState.waiting_for_command],
)
async def regions_handler(
    query: types.CallbackQuery,
    callback_data: Dict[str, str],
    state: FSMContext,
):
    """
    This handler will be called when the user sends
    query with "region" action
    """
    await state.update_data(region=callback_data['answer'])
    reservoirs = await bot.db.get_reservoirs_by_region(callback_data['answer'])
    markup = get_markup_with_objs(action='reservoir', objs=reservoirs)
    back_button = types.InlineKeyboardButton(
        'Назад', callback_data=main_cb.new(action='start', answer='_')
    )
    markup.add(back_button)
    await query.message.edit_text(
        'Выберите водохранилище:', reply_markup=markup
    )
    await MainState.waiting_for_reservoir.set()


@dp.callback_query_handler(
    main_cb.filter(action='reservoir'),
    state=[MainState.waiting_for_reservoir, MainState.waiting_for_period],
)
async def reservoirs_handler(
    query: types.CallbackQuery,
    callback_data: Dict[str, str],
    state: FSMContext,
):
    """
    This handler will be called when the user sends
    query with "reservoir" action
    """
    await state.update_data(reservoir=callback_data['answer'])
    data = await state.get_data()
    markup = get_markup_with_items(action='command', items=command_buttons)
    back_button = types.InlineKeyboardButton(
        'Назад',
        callback_data=main_cb.new(action='region', answer=data['region']),
    )
    markup.add(back_button)
    await query.message.edit_text('Выберите команду:', reply_markup=markup)
    await MainState.waiting_for_command.set()


@dp.callback_query_handler(
    main_cb.filter(action='command'),
    state=MainState.waiting_for_command,
)
async def commands_handler(
    query: types.CallbackQuery,
    callback_data: Dict[str, str],
    state: FSMContext,
):
    """
    This handler will be called when the user sends
    query with "command" action
    """
    await state.update_data(command=callback_data['answer'])
    data = await state.get_data()
    markup = get_markup_with_items(action='period', items=time_buttons)
    back_button = types.InlineKeyboardButton(
        'Назад',
        callback_data=main_cb.new(
            action='reservoir', answer=data['reservoir']
        ),
    )
    markup.add(back_button)
    await query.message.edit_text('Выберите период:', reply_markup=markup)
    await MainState.waiting_for_period.set()


@dp.callback_query_handler(
    main_cb.filter(action='period'),
    state=MainState.waiting_for_period,
)
async def period_handler(
    query: types.CallbackQuery,
    callback_data: Dict[str, str],
    state: FSMContext,
):
    """
    This handler will be called when the user sends
    query with "period" action
    """
    period = callback_data['answer']
    if not period.isdigit():
        await MainState.waiting_for_date1.set()
        return await query.message.edit_text(
            'Введите первую дату периода в формате yyyy.mm.dd:'
        )
    try:
        data = await state.get_data()
        reservoir = await bot.db.get_reservoir_by_slug(data['reservoir'])
        date2 = dt.date.today()
        date1 = date2 - dt.timedelta(int(period))
        pic, caption = await plot_graph(
            reservoir, data['command'], (date1, date2)
        )
    except (KeyError, TypeError, NoDataError) as error:
        logging.error(repr(error))
        await query.message.edit_text('Упс.. что-то пошло не так.')
    else:
        await query.message.answer_photo(
            pic, caption, disable_notification=True
        )
        await query.message.delete()
    finally:
        await state.finish()


@dp.message_handler(state=MainState.waiting_for_date1)
async def manually_input_date1_handler(
    message: types.Message, state: FSMContext
):
    """
    This handler will be called when the user sets
    the waiting_for_date1 state
    """
    try:
        date = parse(message.text)
    except ParserError as error:
        logging.error(repr(error))
        return await message.reply('Попробуйте ещё раз в формате yyyy.mm.dd:')
    await state.update_data(date1=date.date())
    await MainState.waiting_for_date2.set()
    return await message.answer(
        'Введите вторую дату периода в формате yyyy.mm.dd:'
    )


@dp.message_handler(state=MainState.waiting_for_date2)
async def manually_input_date2_handler(
    message: types.Message, state: FSMContext
):
    """
    This handler will be called when the user sets
    the waiting_for_date2 state
    """
    try:
        date = parse(message.text)
        data = await state.get_data()
        reservoir = await bot.db.get_reservoir_by_slug(data['reservoir'])
        pic, caption = await plot_graph(
            reservoir, data['command'], (data['date1'], date.date())
        )
        await message.answer_photo(pic, caption, disable_notification=True)
    except ParserError as error:
        logging.error(repr(error))
        await message.reply('Попробуйте ещё раз в формате yyyy.mm.dd:')
    except NoDataError as error:
        logging.error(repr(error))
        await message.answer('Нет данных за указанный период времени.')
    await state.finish()


async def plot_graph(
    reservoir: Reservoir, command: str, period: Tuple[dt.date]
):
    """
    This function return a photo with a graph
    """
    water_situations = await bot.db.get_water_situations_by_date(
        reservoir, min(period), max(period)
    )
    if len(water_situations) == 0:
        raise NoDataError('Нет данных за указанный период.')

    date1, date2 = water_situations[0].date, water_situations[-1].date
    x = [ws.date for ws in water_situations]
    y = [getattr(ws, command) for ws in water_situations]
    title = (
        f'{reservoir.name} водохранилище\n'
        f'ФПУ={reservoir.force_level} м, '
        f'НПУ={reservoir.normal_level} м, '
        f'УМО={reservoir.dead_level} м'
    )
    caption = (
        f'График за период с {date1.strftime("%d.%m.%Y")} '
        f'по {date2.strftime("%d.%m.%Y")}'
    )
    return await plotter(x, y, title, command), caption


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(bot.db.setup())
        executor.start_polling(dp, skip_updates=True, loop=loop)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        loop.run_until_complete(bot.db.stop())
