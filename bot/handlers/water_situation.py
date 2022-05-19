import datetime as dt
import logging
from typing import Dict

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from dateutil.parser import parse, ParserError
from peewee_async import Manager

from bot.exceptions import NoDataError
from bot.handlers.common import MainState
from bot.markups import main_cb
from db.models import database, ReservoirModel
from utils.plotter import plot_graph


objects = Manager(database)
objects.database.allow_sync = logging.ERROR


def register_water_situation_handlers(dp: Dispatcher):
    dp.register_message_handler(input_date1, state=MainState.waiting_for_date1)
    dp.register_message_handler(input_date2, state=MainState.waiting_for_date2)
    dp.register_callback_query_handler(
        period,
        main_cb.filter(action='period'),
        state=MainState.waiting_for_period,
    )


async def period(
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
        reservoir = await objects.get(ReservoirModel, slug=data['reservoir'])
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


async def input_date1(message: types.Message, state: FSMContext):
    """
    This handler will be called when the user sets
    the waiting_for_date1 state
    """
    try:
        date = parse(message.text)
    except ParserError as error:
        logging.error(repr(error))
        return await message.reply(
            'Попробуйте ещё раз в формате yyyy.mm.dd:',
            disable_notification=True,
        )
    await state.update_data(date1=date.date())
    await MainState.waiting_for_date2.set()
    return await message.answer(
        'Введите вторую дату периода в формате yyyy.mm.dd:',
        disable_notification=True,
    )


async def input_date2(message: types.Message, state: FSMContext):
    """
    This handler will be called when the user sets
    the waiting_for_date2 state
    """
    try:
        date = parse(message.text)
        data = await state.get_data()
        reservoir = await objects.get(ReservoirModel, slug=data['reservoir'])
        pic, caption = await plot_graph(
            reservoir, data['command'], (data['date1'], date.date())
        )
        await message.answer_photo(pic, caption, disable_notification=True)
    except ParserError as error:
        logging.error(repr(error))
        await message.reply(
            'Попробуйте ещё раз в формате yyyy.mm.dd:',
            disable_notification=True,
        )
    except NoDataError as error:
        logging.error(repr(error))
        await message.answer(
            'Нет данных за указанный период времени.',
            disable_notification=True,
        )
    await state.finish()
