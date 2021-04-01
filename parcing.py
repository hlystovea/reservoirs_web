﻿import re
import sqlite3
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup


def parcing_bwu():
    # Парсинг сайта Енисейского БВУ
    url = 'http://enbvu.ru/i03_deyatelnost/i03.07_vdho.php'

    page = requests.get(url)

    soup = BeautifulSoup(page.text, 'html.parser')
    data = soup.find_all(string=re.compile('верхний бьеф'))
    inflow_sayan = soup.find_all(string=re.compile('приток [0-9]'))
    inflow_kras_bratsk = soup.find_all(string=re.compile('приток общий'))
    inflow_kras = inflow_kras_bratsk[0::2]
    inflow_bratsk = inflow_kras_bratsk[1::2]
    parcings_dates = soup.find_all(
        string=re.compile('[0-3]?[0-9][.][01][0-9][.][2][0][2-9][0-9].[г.]')
        )
    print(parcings_dates)
    # Добавление данных об уровнях водохранилищ в базу данных
    # Подключение к базе данных
    conn = sqlite3.connect('levels.sqlite')
    cursor = conn.cursor()

    for i in range(0, 5):  # Итерации по 5 строкам парсинга
        date_str = parcings_dates[i].split()[0]
        try:
            date = datetime.strptime(date_str, '%d.%m.%Y').timestamp()
        except ValueError as error:
            print(f'Произошла ошибка: {error}')
            break
        levels = []
        levels.append(date)
        outflows = []
        outflows.append(date)
        inflows = []
        inflows = [
            date,
            int(inflow_sayan[i].split()[2]),
            int(inflow_kras[i].split()[3]),
            int(inflow_bratsk[i].split()[3])
        ]
        for n in range(0, 6):  # Подготовка строки для записи в бд
            level = data[i*6+n].split()[3]
            level = float(level.replace(',', '.'))
            levels.append(level)
            outflow = int(data[i*6+n].split()[13])
            outflows.append(outflow)
        try:
            cursor.execute(
                'INSERT INTO uvb VALUES(?, ?, ?, ?, ?, ?, ?);',
                tuple(levels),
                )
            cursor.execute(
                'INSERT INTO outflow VALUES(?, ?, ?, ?, ?, ?, ?);',
                tuple(outflows),
                )
            cursor.execute(
                'INSERT INTO inflow VALUES(?, ?, ?, ?);',
                tuple(inflows),
                )
        except sqlite3.IntegrityError as error:
            continue
        else:
            print(f'Добавлены данные за {date_str}')
            conn.commit()
    cursor.close()
    conn.close()


def timer():
    while True:
        parcing_bwu()
        time.sleep(10800)


if __name__ == '__main__':
    timer()
