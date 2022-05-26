import asyncio
import logging
from logging.handlers import RotatingFileHandler
from random import randint
from os import environ

from peewee_async import Manager

from db.models import database
from parsers import AbstractParser, GismeteoParser, KrasParser, RushydroParser

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

    async def _looper(self):
        while self.is_running:
            await self.parser.worker()
            logging.info(f'{self.__class__.__name__} worker sleep')
            await asyncio.sleep(self.sleep_time)

    async def start(self):
        self.is_running = True
        logging.info(f'{self.__class__.__name__} start worker')
        await self._looper()

    async def stop(self):
        logging.info(f'{self.__class__.__name__} stop worker')
        self.is_running = False


async def main():
    objects = Manager(database)
    objects.database.allow_sync = logging.ERROR

    rushydro_parser = RushydroParser(objects)
    kras_parser = KrasParser(objects)
    gismeteo_parser = GismeteoParser(objects)

    rh_crawler = Crawler(rushydro_parser, SLEEP_TIME + randint(5, 10))
    kras_crawler = Crawler(kras_parser, SLEEP_TIME + randint(5, 10))
    gismeteo_crawler = Crawler(gismeteo_parser, 10800)

    await asyncio.gather(
        rh_crawler.start(),
        kras_crawler.start(),
        gismeteo_crawler.start(),
    )


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info('stop')
