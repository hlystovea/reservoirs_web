import asyncio
import datetime as dt
import logging
from logging.handlers import RotatingFileHandler
from os import environ
from typing import List

from aiohttp import ClientError, ClientSession

from db.postgres import PostgresDB
from db.schemas import WaterSituation
from parsers import AbstractParser, KrasParser, RushydroParser


DATABASE_URL = environ.get('DATABASE_URL')
SLEEP_TIME = int(environ.get('SLEEP_TIME', 3600))


rotate_file_handler = RotatingFileHandler('logs/parsing.log', 5000000, 2)
console_out_hundler = logging.StreamHandler()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(funcName)s: %(message)s',
    handlers=[rotate_file_handler, console_out_hundler],
)


class Crawler:
    def __init__(
        self,
        db: PostgresDB,
        parser: AbstractParser,
        sleep_time: int = 3600
    ):
        self.db = db
        self.parser = parser
        self.sleep_time = sleep_time
        self.is_running: bool = False

    async def get_date(self):
        date = await self.db.get_last_date()
        return date or self.parser.first_date

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
                    count += 1
                except Exception as error:
                    logging.error(repr(error))
                    continue
            self.last_date = obj.date
        logging.info(f'{self.__class__.__name__} saved {count} new records')

    async def _worker(self):
        async with ClientSession() as session:
            date = await self.get_date()
            reservoirs = await self.db.get_all_reservoirs()
            while date <= dt.date.today():
                try:
                    page = await self.get_page(session, date=date)
                    objs = await self.parser.parsing(
                        page, date=date, reservoirs=reservoirs
                    )
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
    kras_parser = KrasParser()
    rh_crawler = Crawler(db, rh_parser, SLEEP_TIME)
    kras_crawler = Crawler(db, kras_parser, SLEEP_TIME)
    await asyncio.gather(rh_crawler.start(), kras_crawler.start())


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info('stop')
