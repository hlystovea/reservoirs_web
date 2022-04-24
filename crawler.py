import asyncio
import datetime as dt
import logging
from logging.handlers import RotatingFileHandler
from os import environ
from typing import List

from aiohttp import ClientError, ClientSession

from db.postgres import PostgresDB
from db.schemas import WaterSituation
from parsers import AbstractParser, RushydroParser

DATABASE_URL = environ.get('DATABASE_URL')
SLEEP_TIME = int(environ.get('SLEEP_TIME', 3600))
RH_LAST_DATE = environ.get('RH_LAST_DATE')
if RH_LAST_DATE:
    RH_LAST_DATE = dt.datetime.strptime(RH_LAST_DATE, '%d.%m.%Y').date()


rotate_file_handler = RotatingFileHandler('logs/parsing.log', 5000000, 2)
console_out_hundler = logging.StreamHandler()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(funcName)s: %(message)s',
    handlers=[rotate_file_handler, console_out_hundler],
)


class Crawler:
    def __init__(
        self, db: PostgresDB,
        parser: AbstractParser,
        sleep_time: int,
        last_date: dt.date = None
    ):
        self.db = db
        self.parser = parser
        self.sleep_time = sleep_time
        self.last_date = last_date
        self.is_running: bool = False

    async def set_last_date(self):
        reservoir = await self.db.get_reservoir_by_slug(slug=self.parser.slug)
        self.last_date = await self.db.get_last_date(reservoir)
        if not self.last_date:
            self.last_date = self.parser.last_date

    async def get_page(self, session: ClientSession, **kwargs) -> str:
        url = await self.parser.get_url(**kwargs)
        async with session.get(url=url, ssl=False) as r:
            return await r.text()

    async def save(self, objs: List[WaterSituation]):
        count = 0
        for obj in objs:
            if not await self.db.check_existence(obj):
                try:
                    await self.db.insert_one(obj)
                    self.last_date = obj.date
                    count += 1
                except Exception as error:
                    logging.error(repr(error))
        logging.info(f'{self.__class__.__name__} saved {count} new records')

    async def _worker(self):
        async with ClientSession() as session:
            date = self.last_date - dt.timedelta(days=2)
            reservoirs = await self.db.get_all_reservoirs()
            while self.last_date < dt.date.today() and date <= dt.date.today():
                try:
                    page = await self.get_page(session, date=date)
                    objs = await self.parser.parsing(page, reservoirs)
                    await self.save(objs)
                except (ValueError, AttributeError, ClientError) as error:
                    logging.error(repr(error))
                date += dt.timedelta(days=1)
                await asyncio.sleep(1)

    async def _looper(self):
        while self.is_running:
            await self._worker()
            logging.info(f'{self.__class__.__name__} worker sleep')
            await asyncio.sleep(self.sleep_time)

    async def start(self):
        await self.db.setup()
        if self.last_date is None:
            await self.set_last_date()
        self.is_running = True
        logging.info(f'{self.__class__.__name__} start worker')
        await self._looper()

    async def stop(self):
        logging.info(f'{self.__class__.__name__} stop worker')
        self.is_running = False
        await self.db.stop()


async def main():
    db = PostgresDB(DATABASE_URL)
    rh_parser = RushydroParser()
    rh_crawler = Crawler(db, rh_parser, SLEEP_TIME, RH_LAST_DATE)
    await asyncio.gather(rh_crawler.start())


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info('stop')
