import asyncio
import datetime
import logging
from logging.handlers import RotatingFileHandler
from os import environ
from typing import Dict, List, Optional

import aiohttp
from bs4 import BeautifulSoup
from bs4.element import ResultSet
from pydantic import ValidationError

from db.postgres import PostgresDB
from db.schemas import Reservoir, WaterSituation

DATABASE_URL = environ.get('DATABASE_URL')
DATE_FORMAT = environ.get('DATE_FORMAT', '%d.%m.%Y')
BASE_URL = environ.get('BASE_URL', 'http://www.rushydro.ru/hydrology/informer')
SLEEP_TIME = int(environ.get('SLEEP_TIME', 3600))
DELAY = int(environ.get('DELAY', 2))


rotate_file_handler = RotatingFileHandler('logs/parsing.log', 5000000, 2)
console_out_hundler = logging.StreamHandler()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(funcName)s: %(message)s',
    handlers=[rotate_file_handler, console_out_hundler],
)


class Crawler:
    def __init__(self, db: PostgresDB, delay: int, sleep_time: int):
        self.delay: int = delay
        self.sleep_time: int = sleep_time
        self.is_running: Optional[bool] = False
        self.db: PostgresDB = db
        self._crawler_task: Optional[asyncio.Task] = None

    async def start(self):
        await self.db.setup()
        self.is_running = True
        self._crawler_task = asyncio.create_task(self._worker())
        logging.info('Start crawler')
        await self._crawler_task

    async def get_list_dates(self) -> List[datetime.date]:
        last_date = await self.db.get_last_date() or datetime.date(2013, 4, 13)
        num_days = (datetime.date.today() - last_date).days
        return [last_date + datetime.timedelta(d) for d in range(num_days + 1)]

    async def save_to_db(self, objs: List[WaterSituation]):
        count = 0
        for obj in objs:
            if not await self.db.check_existence(obj):
                try:
                    await self.db.insert_one(obj)
                    count += 1
                except Exception as error:
                    logging.error(repr(error))
        logging.info(f'Saved {count} new records')

    async def values_normalizer(self, values: ResultSet) -> Dict:
        keys = ['level', 'free_capacity', 'inflow', 'outflow', 'spillway']
        values = [v.text.split()[0].split('м')[0] for v in values]
        return dict(zip(keys, values))

    async def parser(self, page: str, reservoirs: List[Reservoir]) -> List[WaterSituation]:  # noqa (E501)
        logging.info('Start parser')
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
            normalized_values = await self.values_normalizer(num_values[3:])
            normalized_values['date'] = date
            normalized_values['reservoir_id'] = reservoir.id
            try:
                instance = WaterSituation.parse_obj(normalized_values)
            except ValidationError as error:
                logging.error(f'{reservoir.slug}: {repr(error)}')
            else:
                result.append(instance)
        logging.info('Stop parser')
        return result

    async def _worker(self):
        while self.is_running:
            dates = await self.get_list_dates()
            reservoirs = await self.db.get_all_reservoirs()
            async with aiohttp.ClientSession() as session:
                for date in dates:
                    url = f'{BASE_URL}/?date={date.isoformat()}'
                    async with session.get(url=url, ssl=False) as resp:
                        page = await resp.text()
                    try:
                        water_situations = await self.parser(page, reservoirs)
                        await self.save_to_db(water_situations)
                    except ValueError as error:
                        logging.error(repr(error))
                    await asyncio.sleep(self.delay)
            logging.info('Sleep crawler')
            await asyncio.sleep(self.sleep_time)

    async def stop(self):
        self.is_running = False
        await self._crawler_task.cancel()
        await self.db.stop()
        logging.info('Stop crawler')


async def main():
    db = PostgresDB(DATABASE_URL)
    crawler = Crawler(db, DELAY, SLEEP_TIME)
    await crawler.start()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info('Stop crawler')
