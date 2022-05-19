from typing import Dict, List, Union

from aiogram import types
from aiogram.utils.callback_data import CallbackData

from db.models import RegionModel, ReservoirModel


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
    'info': 'Морфометрия водохранилища',
}

main_cb = CallbackData('main', 'action', 'answer')


def get_markup_with_objs(
    action: str, objs: List[Union[ReservoirModel, RegionModel]]
):
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
