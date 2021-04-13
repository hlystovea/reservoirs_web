import re
import sqlite3
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup


def db_saver(records: dict):
    conn = sqlite3.connect('levels.sqlite')
    cursor = conn.cursor()
    for i in range(len(records['levels'])):
        try:
            sql_level = '''\
                INSERT INTO uvb
                VALUES(?, ?, ?, ?, ?, ?, ?)
                '''
            cursor.execute(sql_level, records['levels'][i])
            sql_outflow = '''\
                INSERT INTO outflow
                VALUES(?, ?, ?, ?, ?, ?, ?)
                '''
            cursor.execute(sql_outflow, records['outflows'][i])
            sql_inflow = '''\
                INSERT INTO inflow (date, sayany, kras, bratsk)
                VALUES (?, ?, ?, ?)
                '''
            cursor.execute(sql_inflow, records['inflows'][i])
        except sqlite3.IntegrityError:
            continue
        else:
            print(f'Добавлены данные за {records[0][0]}')
            conn.commit()
    cursor.close()
    conn.close()


def parcing(url: str) -> dict:
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')

    data = soup.find_all(string=re.compile('верхний бьеф'))

    inflow_sayan = soup.find_all(string=re.compile('приток [0-9]'))
    inflow_kras_bratsk = soup.find_all(string=re.compile('приток общий'))
    inflow_kras = inflow_kras_bratsk[0::2]
    inflow_bratsk = inflow_kras_bratsk[1::2]

    date_re = '[0-3]?[0-9][.][01][0-9][.][2][0][2-9][0-9].[г.]'
    dates = soup.find_all(string=re.compile(date_re))

    levels = []
    outflows = []
    inflows = []

    for day in range(len(dates)):
        try:
            date = dates[day].split()[0]
            date = datetime.strptime(date, '%d.%m.%Y').timestamp()
        except ValueError as error:
            print(f'Произошла ошибка: {error}')
            break

        lvls = [level.split()[3] for level in data[day*6:day*6+6]]
        lvls = [float(level.replace(',', '.')) for level in lvls]
        lvls.insert(0, date)

        outflws = [outflow.split()[13] for outflow in data[day*6:day*6+6]]
        outflws = [int(outflow) for outflow in outflws]
        outflws.insert(0, date)

        inflws = [
            date,
            int(inflow_sayan[day].split()[2]),
            int(inflow_kras[day].split()[3]),
            int(inflow_bratsk[day].split()[3])
        ]
        levels.append(tuple(lvls))
        outflows.append(tuple(outflws))
        inflows.append(tuple(inflws))

    records = {
        'levels': tuple(levels),
        'outflows': tuple(outflows),
        'inflows': tuple(inflows),
    }
    return records


def timer():
    while True:
        url = 'http://enbvu.ru/i03_deyatelnost/i03.07_vdho.php'
        db_saver(parcing(url))
        time.sleep(3000)


if __name__ == '__main__':
    timer()
