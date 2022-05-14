import asyncio
import datetime as dt
import logging
from logging.handlers import RotatingFileHandler
from os import environ

from aiohttp import ClientError, ClientSession

from db.postgres import PostgresDB
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
        parser: AbstractParser,
        sleep_time: int = 3600
    ):
        self.parser = parser
        self.sleep_time = sleep_time
        self.is_running: bool = False

    async def get_page(self, session: ClientSession, date: dt.date) -> str:
        url = await self.parser.get_url(date)
        async with session.get(url=url, ssl=False) as r:
            return await r.text()

    async def _worker(self):
        async with ClientSession() as session:
            date = await self.parser.get_date()
            while date <= dt.date.today():
                try:
                    page = await self.get_page(session, date=date)
                    objs = await self.parser.parsing(page, date=date)
                    await self.parser.save(objs)
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
        await self.parser.db.setup()
        self.is_running = True
        logging.info(f'{self.__class__.__name__} start worker')
        await self._looper()

    async def stop(self):
        logging.info(f'{self.__class__.__name__} stop worker')
        self.is_running = False
        await self.parser.db.stop()


async def main():
    db = PostgresDB(DATABASE_URL)
    rushydro_parser = RushydroParser(db)
    kras_parser = KrasParser(db)
    rh_crawler = Crawler(rushydro_parser, SLEEP_TIME)
    kras_crawler = Crawler(kras_parser, SLEEP_TIME)
    await asyncio.gather(rh_crawler.start(), kras_crawler.start())


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info('stop')
