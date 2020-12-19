import requests
import re
import sqlite3
import time

from datetime import datetime
from bs4 import BeautifulSoup


def parcing_bwu():
    # Парсинг сайта Енисейского БВУ
    url = 'http://enbvu.ru/i03_deyatelnost/i03.07_vdho.php'

    page = requests.get(url)

    soup = BeautifulSoup(page.text, 'html.parser')
    parcings_levels = soup.find_all(string=re.compile('верхний бьеф'))
    parcings_flow1 = soup.find_all(string=re.compile('приток [0-9]'))
    parcings_flow2 = soup.find_all(string=re.compile('приток общий'))
    for z in range(len(parcings_flow1)):
        print(parcings_flow1[z])
    for z in range(len(parcings_flow2)):
        print(parcings_flow2[z])
    parcings_dates = soup.find_all(
        string=re.compile('[0-3][0-9][.][01][0-9][.][2][0][2-9][0-9].[г.]')
        )

    # Добавление данных об уровнях водохранилищ в базу данных
    # Подключение к базе данных
    conn = sqlite3.connect('levels.sqlite')
    cursor = conn.cursor()

    for i in range(0, 5):  # Итерации по 5 строкам парсинга
        date = parcings_dates[i].split()[0]
        date = datetime.strptime(date, '%d.%m.%Y')
        date = datetime.date(date)
        values = []
        val = []
        values.append(str(date))
        val.append(str(date))
        for n in range(0, 6):  # Подготовка строки для записи в бд
            level = (parcings_levels[i*6+n].split()[3])
            avg_flow = (parcings_levels[i*6+n].split()[13])
            level = float(level.replace(',', '.'))
            values.append(level)
            val.append(avg_flow)
        print(val)
        print(values)
        try:
            cursor.execute(
                'INSERT INTO uvb VALUES(?, ?, ?, ?, ?, ?, ?);',
                tuple(values)
                )
            conn.commit()
            print(f'Добавлены данные за {date}')
        except sqlite3.IntegrityError:
            continue
    cursor.close()
    conn.close()


def timer():
    while True:
        parcing_bwu()
        time.sleep(10800)


if __name__ == '__main__':
    timer()
