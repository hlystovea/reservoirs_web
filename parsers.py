import logging
import datetime as dt
import re
from abc import ABCMeta, abstractmethod
from logging.handlers import RotatingFileHandler
from os import environ
from typing import Dict, List

from bs4 import BeautifulSoup
from bs4.element import ResultSet
from pydantic import ValidationError

from db.postgres import PostgresDB
from db.schemas import WaterSituation


rotate_file_handler = RotatingFileHandler('logs/parsing.log', 5000000, 2)
console_out_hundler = logging.StreamHandler()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(funcName)s: %(message)s',
    handlers=[rotate_file_handler, console_out_hundler],
)


class AbstractParser(metaclass=ABCMeta):
    db: PostgresDB
    slug: str
    base_url: str
    first_date: dt.date

    @abstractmethod
    def get_date(self) -> dt.date:
        pass

    @abstractmethod
    def get_url(self) -> str:
        pass

    @abstractmethod
    def preprocessing(self) -> Dict:
        pass

    @abstractmethod
    def parsing(self):
        pass

    @abstractmethod
    def save(self):
        pass


class WaterSituationMixin(AbstractParser):
    def __init__(self, db):
        self.db = db

    async def get_date(self):
        date = await self.db.get_last_date()
        return date or self.first_date

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
        logging.info(f'{self.__class__.__name__} saved {count} new records')


class RushydroParser(WaterSituationMixin):
    slug: str = 'sayano'
    first_date: dt.date = dt.date(2013, 4, 13)
    base_url: str = environ.get(
        'RUSHYDRO_URL', 'http://www.rushydro.ru/hydrology/informer'
    )

    async def get_url(self, date: dt.date) -> str:
        return f'{self.base_url}/?date={date.isoformat()}'

    async def preprocessing(self, values: ResultSet) -> Dict:
        keys = ['level', 'free_capacity', 'inflow', 'outflow', 'spillway']
        values = [v.text.split()[0].split('м')[0] for v in values]
        return dict(zip(keys, values))

    async def parsing(self, page: str, **kwargs) -> List[WaterSituation]:
        logging.info(f'{self.__class__.__name__} start parsing')

        soup = BeautifulSoup(page, 'html.parser')
        date_str = soup.find('input', id='popupDatepicker').get('value')
        date = dt.datetime.strptime(date_str, '%d.%m.%Y').date()
        logging.info(f'{self.__class__.__name__} parsed date - {date}')

        result = []
        for reservoir in await self.db.get_all_reservoirs():
            informer_data = soup.find(
                'div',
                class_=f'informer-block {reservoir.slug}',
            )
            if informer_data is None:
                continue
            num_values = informer_data.find_all('b')
            normalized_values = await self.preprocessing(num_values[3:])
            normalized_values['date'] = date
            normalized_values['reservoir_id'] = reservoir.id
            try:
                instance = WaterSituation.parse_obj(normalized_values)
            except ValidationError as error:
                logging.error(f'{reservoir.slug}: {repr(error)}')
            else:
                result.append(instance)
        logging.info(f'{self.__class__.__name__} stop parsing')
        return result


class KrasParser(WaterSituationMixin):
    slug: str = 'kras'
    first_date: dt.date = dt.date(2021, 7, 1)
    base_url: str = environ.get('KRAS_URL', 'http://enbvu.ru/i03_deyatelnost')

    month_names: dict = {
        1: 'jan',
        2: 'feb',
        3: 'mar',
        4: 'apr',
        5: 'may',
        6: 'iun',
        7: 'iul',
        8: 'aug',
        9: 'sep',
        10: 'okt',
        11: 'nov',
        12: 'dec',
    }

    async def get_url(self, date: dt.date) -> str:
        num_year = date.year - self.first_date.year
        num_month = date.month - self.first_date.month
        page_number = num_year * 12 + num_month + 1

        return self.base_url + '/i03.07.{0:=02}_{1}.php'.format(
            page_number, self.month_names[date.month]
        )

    async def preprocessing(self, values: ResultSet) -> Dict:
        keys = ['level', 'inflow', 'outflow', 'spillway']
        values = [float(v.replace(",", ".")) for v in values]
        return dict(zip(keys, values))

    async def parsing(self, page: str, date: dt.date) -> List[WaterSituation]:
        logging.info(f'{self.__class__.__name__} start parsing')

        soup = BeautifulSoup(page, 'html.parser')
        iul_class = soup.find_all('div', class_='iul_day_1')
        reservoir = await self.db.get_reservoir_by_slug(self.slug)

        result = []
        for block in iul_class:
            if not block.find('div', class_='date'):
                continue
            parsed_date = dt.date(
                year=date.year,
                month=date.month,
                day=int(block.get('id').split('_')[-1])
            )
            logging.info(f'{self.__class__.__name__} parsed date {parsed_date}')  # noqa(E501)

            level_str = block.find_all(string=re.compile('верхний бьеф'))[2]
            inflow_str = block.find_all(string=re.compile('приток общий'))[0]
            spillway_str = block.find_all(string=re.compile('холостой сброс'))[2]  # noqa(E501)

            integer = re.compile(r'[0-9]+')
            floating = re.compile(r'[0-9]+,[0-9]+')

            level = floating.findall(level_str)[0]
            outflow = integer.findall(level_str)[-1]
            inflow = integer.findall(inflow_str)[0]
            spillway = integer.findall(spillway_str)[0]

            num_values = [level, inflow, outflow, spillway]
            normalized_values = await self.preprocessing(num_values)
            normalized_values['date'] = parsed_date
            normalized_values['reservoir_id'] = reservoir.id
            try:
                instance = WaterSituation.parse_obj(normalized_values)
            except ValidationError as error:
                logging.error(f'{reservoir.slug}: {repr(error)}')
            else:
                result.append(instance)
        logging.info(f'{self.__class__.__name__} stop parsing')
        return result
