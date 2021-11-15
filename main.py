import logging
import os
import re
import time
from datetime import date, timedelta
from logging.handlers import RotatingFileHandler

import requests
import telebot
from telebot.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           ReplyKeyboardMarkup, ReplyKeyboardRemove)

from utils import Plotter, Reservoir, TimePeriod, res_param


TOKEN = os.environ.get('BOT_BWU')

bot = telebot.TeleBot(TOKEN)

logger = telebot.logger
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s %(funcName)s - %(message)s')
rf_handler = RotatingFileHandler('bot.log', maxBytes=5000000, backupCount=2)
rf_handler.setFormatter(formatter)
logger.addHandler(rf_handler)


class Graph():
    def __init__(self, reservoir) -> None:
        self.reservoir = reservoir
        self.param = None
        self.period = None


graph_buffer = {}


start_keyboard = ReplyKeyboardMarkup(True, selective=True)
start_keyboard.row('Показать список водохранилищ')


res_keyboard = InlineKeyboardMarkup()
for res in sorted(res_param):
    button = InlineKeyboardButton(
        res_param[res][0],
        callback_data=res,
    )
    res_keyboard.add(button)


command_buttons = {
    'levels': 'Построить график УВБ',
    'inflow': 'Построить график притока',
    'outflow': 'Построить график сброса',
    'info': 'Информация о водохранилище',
    'back_to_reservoirs': 'Назад',
}

command_keyboard = InlineKeyboardMarkup()
for command in command_buttons:
    button = InlineKeyboardButton(
        command_buttons[command],
        callback_data=command,
    )
    command_keyboard.add(button)


time_keyboard = InlineKeyboardMarkup()
week = InlineKeyboardButton('Неделя', callback_data='fixed&7')
month = InlineKeyboardButton('Месяц', callback_data='fixed&30')
six_month = InlineKeyboardButton('Пол года', callback_data='fixed&183')
year = InlineKeyboardButton('Год', callback_data='fixed&365')
all_time = InlineKeyboardButton('За всё время', callback_data='fixed&10000')
manual = InlineKeyboardButton('Ввести даты вручную', callback_data='manually')
back = InlineKeyboardButton('Назад', callback_data='back_to_commands')
time_keyboard.row(week, month, six_month, year)
time_keyboard.add(all_time).add(manual).add(back)


# Start message
@bot.message_handler(commands=['start', 'help'])
def start(message):
    text = ('Привет! Я бот, который умеет по данным [Енисейского БВУ]'
            '(http://enbvu.ru/i03_deyatelnost/i03.07_vdho.php) строить '
            'графики УВБ, сброса и притока воды в водохранилища '
            'Ангаро-Енисейского каскада ГЭС. '
            'Чтобы начать, нажмите *"Показать список водохранилищ"*.')
    bot.send_message(
        message.chat.id,
        text,
        reply_markup=start_keyboard,
        parse_mode='Markdown',
        disable_web_page_preview=True,
    )


@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    logger.info(call.data)
    bot.answer_callback_query(call.id, 'Секунду..')
    if call.data in res_param:
        reservoir = Reservoir(call.data)
        graph = Graph(reservoir)
        graph_buffer[call.message.chat.id] = graph
        text = 'Выберите команду:'
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=command_keyboard,
        )
    elif call.data == 'info':
        text = 'Раздел находится в разработке.'
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
        )
    elif call.data == 'manually':
        text = ('Введите начало и конец периода '
                'через пробел в формате dd.mm.yyyy')
        msg = bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
        )
        bot.register_next_step_handler(msg, manually_input_step)
    elif 'fixed' in call.data:
        graph = graph_buffer[call.message.chat.id]
        days = int(call.data.split('&')[1])
        date2 = date.today()
        date1 = date2 - timedelta(days)
        period = TimePeriod(
            date1.isoformat(),
            date2.isoformat(),
            date_format='%Y-%m-%d',
        )
        graph.period = period
        pic, text, is_success = plotting_graph(graph)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        if is_success:
            bot.send_photo(call.message.chat.id, pic, text)
        else:
            bot.send_message(call.message.chat.id, text)
    elif call.data in ('levels', 'inflow', 'outflow'):
        graph = graph_buffer[call.message.chat.id]
        graph.param = call.data
        text = 'Выберите период, за который необходимо построить график:'
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=time_keyboard,
        )
    elif call.data == 'back_to_reservoirs':
        text = 'Выберите водохранилище:'
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=res_keyboard,
        )
    elif call.data == 'back_to_commands':
        text = 'Выберите водохранилище:'
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=command_keyboard,
        )
    else:
        text = 'Упс.. похоже я не знаю ответ.'
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, text)


def manually_input_step(message):
    try:
        graph = graph_buffer[message.chat.id]
        dates = re.findall(
            r'[0-3][0-9][.][01][0-9][.][12][09][0-9][0-9]',
            message.text,
        )
        date1 = dates[0]
        date2 = None
        if len(dates) > 1:
            date2 = dates[-1]
        period = TimePeriod(date1, date2, date_format='%d.%m.%Y')
        graph.period = period
        pic, text, is_success = plotting_graph(graph)
        if is_success:
            bot.delete_message(message.chat.id, message.message_id-1)
            bot.send_photo(message.chat.id, pic, text)
        else:
            bot.delete_message(message.chat.id, message.message_id-1)
            bot.reply_to(message, text)
    except (ValueError, IndexError) as error:
        logger.error(repr(error))
        text = 'Ошибка в дате, попробуйте ещё раз в формате dd.mm.yyyy'
        msg = bot.reply_to(message, text)
        bot.register_next_step_handler(msg, manually_input_step)


@bot.message_handler(content_types=['text'])
def list_reservoirs(message):
    if message.text.lower() == 'показать список водохранилищ':
        text = 'Выберите водохранилище:'
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(message.chat.id, text, reply_markup=res_keyboard)


def plotting_graph(graph):
    reservoir = graph.reservoir
    param = graph.param
    period = graph.period
    pic = None
    text = 'Упс.. похоже я не знаю ответ.'
    is_success = False
    if param == 'levels':
        pic, text, is_success = Plotter.plot_levels(reservoir, period)
    elif param == 'inflow':
        pic, text, is_success = Plotter.plot_inflow(reservoir, period)
    elif param == 'outflow':
        pic, text, is_success = Plotter.plot_outflow(reservoir, period)
    return pic, text, is_success


if __name__ == '__main__':
    while True:
        try:
            logging.info('Start polling')
            bot.polling()
        except requests.exceptions.ConnectionError as error:
            logging.error(repr(error))
            time.sleep(30)
