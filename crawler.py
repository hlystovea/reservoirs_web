import asyncio
import datetime
import logging
from logging.handlers import RotatingFileHandler
from os import environ
from typing import Dict, List

import aiohttp
from bs4 import BeautifulSoup
from bs4.element import ResultSet
from pydantic import ValidationError

from core.db.connectors import (check_existence, get_all_reservoirs,
                                get_connection, get_last_date, insert_one)
from core.db.schemas import Reservoir, WaterSituation

DATE_FORMAT = environ.get('DATE_FORMAT', '%d.%m.%Y')
BASE_URL = environ.get('BASE_URL', 'http://www.rushydro.ru/hydrology/informer')
SLEEP_TIME = int(environ.get('SLEEP_TIME', 3600))


rotate_file_handler = RotatingFileHandler('logs/parsing.log', 5000000, 2)
console_out_hundler = logging.StreamHandler()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(funcName)s: %(message)s',
    handlers=[rotate_file_handler, console_out_hundler],
)


async def get_list_dates_from(date: datetime.date):
    num_days = (datetime.date.today() - date).days + 1
    dates = [date + datetime.timedelta(d) for d in range(num_days)]
    return dates


async def parser(page: str, reservoirs: List[Reservoir]) -> List[WaterSituation]:  # noqa (E501)
    logging.info('Parser start')
    soup = BeautifulSoup(page, 'html.parser')
    date_str = soup.find('input', id='popupDatepicker').get('value')
    date = datetime.datetime.strptime(date_str, DATE_FORMAT).date()
    logging.info(f'Parsed date: {date}')
    result = []

    for reservoir in reservoirs:
        informer_data = soup.find(
            'div',
            class_=f'informer-block {reservoir.slug}',
        )
        num_values = informer_data.find_all('b')

        normalized_values = await values_normalizer(num_values[3:])
        normalized_values['date'] = date
        normalized_values['reservoir_id'] = reservoir.id

        try:
            instance = WaterSituation.parse_obj(normalized_values)
        except ValidationError as error:
            logging.error(f'{reservoir.slug}: {repr(error)}')
        else:
            result.append(instance)
    logging.info('Parser stop')
    return result


async def values_normalizer(values: ResultSet) -> Dict:
    keys = ['level', 'free_capacity', 'inflow', 'outflow', 'spillway']
    values = [v.text.split()[0].split('м')[0] for v in values]
    return dict(zip(keys, values))


async def save_to_db(conn, objs: List[WaterSituation]):
    count = 0
    for obj in objs:
        if not await check_existence(conn, obj):
            try:
                await insert_one(conn, obj)
                count += 1
            except Exception as error:
                logging.error(repr(error))
    logging.info(f'Saved {count} new records')


async def crawler():
    conn = await get_connection()
    while True:
        logging.info('Crawler start')
        last_date = await get_last_date(conn)
        if last_date is None:
            last_date = datetime.date(2013, 4, 12)
        dates = await get_list_dates_from(last_date)
        reservoirs = await get_all_reservoirs(conn)
        async with aiohttp.ClientSession() as session:
            for date in dates:
                url = f'{BASE_URL}/?date={date.isoformat()}'
                async with session.get(url=url, ssl=False) as resp:
                    page = await resp.text()
                try:
                    water_situations = await parser(page, reservoirs)
                    await save_to_db(conn, water_situations)
                except ValueError as error:
                    logging.error(repr(error))
                await asyncio.sleep(2)
        logging.info('Crawler sleep')
        await asyncio.sleep(SLEEP_TIME)


if __name__ == '__main__':
    asyncio.run(crawler())
