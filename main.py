import os
from datetime import date, datetime, timedelta

import telebot
from telebot.types import (ForceReply, InlineKeyboardButton,
                           InlineKeyboardMarkup, ReplyKeyboardMarkup)

from plot import plot, res_param

token = os.environ.get('BOT_BWU')
bot = telebot.TeleBot(token)

main_kbrd = ReplyKeyboardMarkup(True, selective=True)
main_kbrd.row('Показать список')

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
        reply_markup=main_kbrd,
        parse_mode='Markdown',
        disable_web_page_preview=True,
    )


# Inputing period manually
@bot.message_handler(regexp='^[0-3][0-9][.][01][0-9][.][12][09][0-9][0-9]$')
def manually_plot(message):
    if ('res' and 'date1') in choice:
        res = choice['res']
        date1 = choice['date1']
        try:
            date2 = datetime.strptime(message.text, '%d.%m.%Y')
            date2 = datetime.date(date2)
            if date1 < date2:
                pic, answer, is_success = plot(res, date1, date2)
            else:
                pic, answer, is_success = plot(res, date2, date1)
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
                    reply_markup=main_kbrd,
                )
                if is_success:
                    bot.send_photo(message.chat.id, pic)
                    with open('level.csv', 'rb') as csv:
                        bot.send_document(message.chat.id, csv)
            choice.clear()
        except ValueError:
            text = 'Ошибка в дате, попробуйте ещё раз'
            bot.send_message(message.chat.id, text, reply_markup=main_kbrd)
    elif 'res' in choice:
        try:
            date1 = datetime.strptime(message.text, '%d.%m.%Y')
            date1 = datetime.date(date1)
            choice['date1'] = date1
            text = 'Введите вторую дату периода в формате dd.mm.yyyy'
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
                    text,
                    reply_markup=ForceReply(),
                )
        except ValueError:
            text = 'Ошибка в дате, попробуйте ещё раз'
            bot.send_message(message.chat.id, text, reply_markup=main_kbrd)
    else:
        text = 'Сначала выберите водохранилище.'
        bot.send_message(message.chat.id, text)


# Choice of reservoir
@bot.message_handler(content_types=['text'])
def list_reservoirs(message):
    keyboard = InlineKeyboardMarkup()
    for r in sorted(res_param):
        button = InlineKeyboardButton(
            res_param[r][0],
            callback_data=f'reservoir {str(r)}',
        )
        keyboard.add(button)
    text = ('Выберите водохранилище, чтобы построить'
            'график уровня верхнего бьефа.')
    if message.text.lower() == 'показать список':
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(message.chat.id, text, reply_markup=keyboard)


# Choice of period and plotting
@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    if 'reservoir' in call.data:
        bot.answer_callback_query(call.id)
        res = int(call.data.split()[1])
        choice['res'] = res

        week = InlineKeyboardButton(text='Неделя', callback_data='fixed 7')
        month = InlineKeyboardButton(text='Месяц', callback_data='fixed 30')
        month3 = InlineKeyboardButton(text='3 месяца', callback_data='fixed 90') # noqa
        year = InlineKeyboardButton(text='Год', callback_data='fixed 365')
        manually = InlineKeyboardButton(text='Ввести даты вручную', callback_data='manually') # noqa

        keyboard = InlineKeyboardMarkup()
        keyboard.row(week, month, month3, year).add(manually)

        text1 = res_param[res][0]
        text2 = 'Выберите период, за который необходимо построить график:'
        bot.edit_message_text(
            text1,
            call.message.chat.id,
            call.message.message_id,
        )
        bot.send_message(call.message.chat.id, text2, reply_markup=keyboard)

    elif 'manually' in call.data:
        text = 'Введите первую дату периода в формате dd.mm.yyyy'
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
        try:
            res = choice['res']
            pic, answer, is_success = plot(res, date1, date2)
            bot.edit_message_text(
                answer,
                call.message.chat.id,
                call.message.message_id,
            )
            bot.send_photo(call.message.chat.id, pic)
        except KeyError:
            text = (
                'Что-то пошло не так. '
                'Попробуйте выбрать водохранилище ещё раз.')
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, text)

    else:
        text = 'Упс.. похоже я не знаю ответ.'
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, text)


bot.polling()
