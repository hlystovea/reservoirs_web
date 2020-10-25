import telebot
import os
import matplotlib.pyplot as plt
from plot import plot
from telebot.types import (InlineKeyboardMarkup, ReplyKeyboardMarkup,
            KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton)


token = os.environ.get('BOT_BWU')
bot = telebot.TeleBot('token')

# выбор водохранилища
@bot.message_handler(commands=['start', 'help'])
def start_message(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton
    (text='Саяно-Шушенское водохранилище', callback_data='1'))
    markup.add(telebot.types.InlineKeyboardButton
    (text='Майнское водохранилище', callback_data='2'))
    markup.add(telebot.types.InlineKeyboardButton
    (text='Красноярское водохранилище', callback_data='3'))
    markup.add(telebot.types.InlineKeyboardButton
    (text='Братское водохранилище', callback_data='4'))
    markup.add(telebot.types.InlineKeyboardButton
    (text='Усть-Илимское водохранилище', callback_data='5'))
    markup.add(telebot.types.InlineKeyboardButton
    (text='Богучанское водохранилище', callback_data='6'))
    text1 = 'Выберите водохранилище, чтобы узнать его уровень:'
    bot.send_message(message.chat.id, text1, reply_markup=markup)

# выбор периода построения графика
@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    res = call.data
    
    keyboard = InlineKeyboardMarkup()
    week = InlineKeyboardButton(text='Неделя', switch_inline_query_current_chat=f'{res} 7')
    month = InlineKeyboardButton(text='Месяц', switch_inline_query_current_chat=f'{res} 30')
    month3 = InlineKeyboardButton(text='3 месяца', switch_inline_query_current_chat=f'{res} 90')
    year = InlineKeyboardButton(text='Год', switch_inline_query_current_chat=f'{res} 365')
    keyboard.row(week, month, month3, year)
    text2 = 'Укажите период, за который необходимо построить график:'
    bot.send_message(call.message.chat.id, text2, reply_markup=keyboard)

# отправка графика
@bot.message_handler(content_types=['text'])
def text_message(message):
    split = message.text.split()
    print(split)
    if len(split) == 3:
        res = split[1]
        days = split[2]
        if res.isdigit() and days.isdigit():
            plot(res, days)
            pic = open('D:/python/bwu/pic.png', 'rb')
            bot.send_photo(message.chat.id, pic)


bot.polling()
