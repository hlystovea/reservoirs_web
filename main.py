import os
import re
from datetime import date, timedelta

import telebot
from telebot.types import (ForceReply, InlineKeyboardButton,
                           InlineKeyboardMarkup, ReplyKeyboardMarkup)

from utils import Plotter, Reservoir, TimePeriod, res_param

TOKEN = os.environ['BOT_BWU']

bot = telebot.TeleBot(TOKEN)

start_keyboard = ReplyKeyboardMarkup(True, selective=True)
start_keyboard.row('Показать список')

res_keyboard = InlineKeyboardMarkup()
for r in sorted(res_param):
    button = InlineKeyboardButton(
        res_param[r][0],
        callback_data=f'reservoir {r}',
    )
    res_keyboard.add(button)

time_keyboard = InlineKeyboardMarkup()
week = InlineKeyboardButton(text='Месяц', callback_data='fixed 30')
month = InlineKeyboardButton(text='Пол года', callback_data='fixed 183')
month3 = InlineKeyboardButton(text='Год', callback_data='fixed 365')
year = InlineKeyboardButton(text='Всё время', callback_data='fixed 10000')
manually = InlineKeyboardButton(text='Ввести даты вручную', callback_data='manually') # noqa
info = InlineKeyboardButton(text='Вывести информацию о ГЭС', callback_data='get_info') # noqa
inflow = InlineKeyboardButton(text='Построить график притока', callback_data='inflow') # noqa
outflow = InlineKeyboardButton(text='Построить график сброса', callback_data='outflow') # noqa
time_keyboard.row(week, month, month3, year).add(manually).add(info).add(inflow).add(outflow) # noqa

choice = {}


# Start message
@bot.message_handler(commands=['start', 'help'])
def start(message):
    text = ('Привет! Я бот, который умеет по данным [Енисейского БВУ]'
            '(http://enbvu.ru/i03_deyatelnost/i03.07_vdho.php) строить '
            'графики уровней водохранилищ Ангаро-Енисейского каскада ГЭС. '
            'Чтобы начать, нажмите *"Показать список"*')
    bot.send_message(
        message.chat.id,
        text,
        reply_markup=start_keyboard,
        parse_mode='Markdown',
        disable_web_page_preview=True,
    )


@bot.message_handler(commands=['stat'])
def statistic(message):
    period = TimePeriod('01.01.1990')
    pic = Plotter.plot_statistics(period)
    bot.delete_message(message.chat.id, message.message_id)
    bot.send_photo(message.chat.id, pic)


# Choice of period and plotting
@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    if 'info' in call.data:
        bot.answer_callback_query(call.id)
        res = Reservoir(choice['res'])
        res.add_statistic()
        text = 'Раздел находится в разработке.'
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
        )
        choice.clear()
    elif 'reservoir' in call.data:
        res = call.data.split()[1]
        choice['res'] = res
        bot.answer_callback_query(call.id)
        text1 = f'{res_param[res][0]}:'
        text2 = 'Выберите период, за который необходимо построить график:'
        bot.edit_message_text(
            text1,
            call.message.chat.id,
            call.message.message_id,
        )
        bot.send_message(
            call.message.chat.id,
            text2,
            reply_markup=time_keyboard
        )
    elif 'manually' in call.data:
        text = 'Введите начало и конец периода через пробел в формате dd.mm.yyyy'
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=ForceReply())
    elif 'fixed' in call.data:
        bot.answer_callback_query(call.id, text='Уже рисую..')
        days = int(call.data.split()[1])
        date2 = date.today()
        date1 = date2 - timedelta(days)
        period = TimePeriod(date1.isoformat(), date2.isoformat(), date_format='%Y-%m-%d')
        try:
            res = Reservoir(choice['res'])
            res.add_statistic()
            pic, answer, is_success = Plotter.plot_levels(res, period)
            bot.edit_message_text(
                answer,
                call.message.chat.id,
                call.message.message_id,
            )
            if is_success:
                bot.send_photo(call.message.chat.id, pic)
        except KeyError:
            text = (
                'Что-то пошло не так. '
                'Попробуйте выбрать водохранилище ещё раз.')
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, text)
        choice.clear()
    elif 'inflow' in call.data:
        bot.answer_callback_query(call.id, text='Уже рисую..')
        period = TimePeriod('01.01.1990')
        try:
            res = Reservoir(choice['res'])
            res.add_statistic()
            pic, answer, is_success = Plotter.plot_inflow(res, period)
            bot.edit_message_text(
                answer,
                call.message.chat.id,
                call.message.message_id,
            )
            if is_success:
                bot.send_photo(call.message.chat.id, pic)
        except KeyError:
            text = (
                'Что-то пошло не так. '
                'Попробуйте выбрать водохранилище ещё раз.')
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, text)
        choice.clear()
    elif 'outflow' in call.data:
        bot.answer_callback_query(call.id, text='Уже рисую..')
        period = TimePeriod('01.01.1990')
        try:
            res = Reservoir(choice['res'])
            res.add_statistic()
            pic, answer, is_success = Plotter.plot_outflow(res, period)
            bot.edit_message_text(
                answer,
                call.message.chat.id,
                call.message.message_id,
            )
            if is_success:
                bot.send_photo(call.message.chat.id, pic)
        except KeyError:
            text = (
                'Что-то пошло не так. '
                'Попробуйте выбрать водохранилище ещё раз.')
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, text)
        choice.clear()
    else:
        text = 'Упс.. похоже я не знаю ответ.'
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, text)


# Inputing period manually
@bot.message_handler(regexp='[0-3][0-9][.][01][0-9][.][12][09][0-9][0-9]')
def manually_plot(message):
    if 'res' in choice:
        try:
            dates = re.findall(
                r'[0-3][0-9][.][01][0-9][.][12][09][0-9][0-9]',
                message.text
            )
            date1 = dates[0]
            date2 = None
            if len(dates) > 1:
                date2 = dates[-1]
            period = TimePeriod(date1, date2, date_format='%d.%m.%Y')
            res = Reservoir(choice['res'])
            res.add_statistic()
            pic, answer, is_success = Plotter.plot_levels(res, period)
            Plotter.save_csv(res, period)
            try:
                bot.delete_message(
                    message.chat.id,
                    message.reply_to_message.message_id,
                )
            except AttributeError:
                pass
            finally:
                bot.delete_message(message.chat.id, message.message_id)
                bot.send_message(
                    message.chat.id,
                    answer,
                    reply_markup=start_keyboard,
                )
                if is_success:
                    bot.send_photo(message.chat.id, pic)
                    with open('level.csv', 'rb') as csv:
                        bot.send_document(message.chat.id, csv)
            choice.clear()
        except ValueError:
            text = 'Ошибка в дате, попробуйте ещё раз в формате dd.mm.yyyy'
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(message.chat.id, text, reply_markup=ForceReply())
    else:
        text = 'Сначала выберите водохранилище'
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(message.chat.id, text)


# Choice of reservoir
@bot.message_handler(content_types=['text'])
def list_reservoirs(message):
    if message.text.lower() == 'показать список':
        text = ('Выберите водохранилище')
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(message.chat.id, text, reply_markup=res_keyboard)


bot.polling()
