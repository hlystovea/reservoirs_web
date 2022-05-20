import asyncio
import datetime as dt
import logging
import re
from abc import ABCMeta, abstractmethod
from logging.handlers import RotatingFileHandler
from os import environ
from typing import Dict, List

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from bs4.element import ResultSet
from peewee import fn, SQL
from peewee_async import Manager
from pydantic import parse_obj_as, ValidationError

from db.models import ReservoirModel, WeatherModel, SituationModel, GeoObjectModel
from db.schemas import Situation, Gismeteo


rotate_file_handler = RotatingFileHandler('logs/parsing.log', 5000000, 2)
console_out_hundler = logging.StreamHandler()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(funcName)s: %(message)s',
    handlers=[rotate_file_handler, console_out_hundler],
)


class AbstractParser(metaclass=ABCMeta):
    objects: Manager
    base_url: str

    @abstractmethod
    def get_date(self) -> dt.date:
        pass

    @abstractmethod
    def get_url(self) -> str:
        pass

    @abstractmethod
    def get_page(self) -> str:
        pass

    @abstractmethod
    def parsing(self):
        pass

    @abstractmethod
    def worker(self):
        pass

    @abstractmethod
    def save(self):
        pass


class SituationMixin(AbstractParser):
    first_date: dt.date = dt.date(2013, 4, 13)

    def __init__(self, objects):
        self.objects = objects

    async def get_date(self):
        date = await self.objects.scalar(
            SituationModel.select(
                fn.Max(SituationModel.date).alias('last_date')
            ).group_by(
                SituationModel.reservoir
            ).order_by(
                SQL('last_date')
            )
        )
        return date or self.first_date

    async def get_page(self, session: ClientSession, date: dt.date) -> str:
        url = await self.get_url(date)
        async with session.get(url=url, ssl=False) as r:
            return await r.text()

    async def worker(self):
        async with ClientSession() as session:
            date = await self.get_date()
            while date <= dt.date.today():
                try:
                    page = await self.get_page(session, date=date)
                    instances = await self.parsing(page, date=date)
                    await self.save(instances)
                except (ValueError, AttributeError) as error:
                    logging.error(repr(error))
                date += dt.timedelta(days=1)
                await asyncio.sleep(1)

    async def save(self, instances: List[Situation]):
        saved_count = 0
        for instance in instances:
            _, created = await self.objects.get_or_create(
                SituationModel,
                date=instance.date,
                reservoir_id=instance.reservoir_id,
                defaults=instance.dict(),
            )
            saved_count += created
        logging.info(f'{self.__class__.__name__} saved {saved_count} new records')


class RushydroParser(SituationMixin):
    base_url: str = environ.get(
        'RUSHYDRO_URL', 'http://www.rushydro.ru/hydrology/informer'
    )

    async def get_url(self, date: dt.date) -> str:
        return f'{self.base_url}/?date={date.isoformat()}'

    async def preprocessing(self, values: ResultSet) -> Dict:
        keys = ['level', 'free_capacity', 'inflow', 'outflow', 'spillway']
        values = [v.text.split()[0].split('м')[0] for v in values]
        return dict(zip(keys, values))

    async def parsing(self, page: str, **kwargs) -> List[Situation]:
        logging.info(f'{self.__class__.__name__} start parsing')

        soup = BeautifulSoup(page, 'html.parser')
        date_str = soup.find('input', id='popupDatepicker').get('value')
        date = dt.datetime.strptime(date_str, '%d.%m.%Y').date()
        logging.info(f'{self.__class__.__name__} parsed date - {date}')

        result = []
        for reservoir in await self.objects.execute(ReservoirModel.select()):
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
                instance = Situation.parse_obj(normalized_values)
            except ValidationError as error:
                logging.error(f'{reservoir.slug}: {repr(error)}')
            else:
                result.append(instance)
        logging.info(f'{self.__class__.__name__} stop parsing')
        return result


class KrasParser(SituationMixin):
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

    async def preprocessing(self, values: List[ResultSet]) -> Dict:
        keys = ['level', 'inflow', 'outflow', 'spillway']
        values = [float(v.replace(",", ".")) for v in values]
        return dict(zip(keys, values))

    async def parsing(self, page: str, date: dt.date) -> List[Situation]:
        logging.info(f'{self.__class__.__name__} start parsing')

        soup = BeautifulSoup(page, 'html.parser')
        iul_class = soup.find_all('div', class_='iul_day_1')
        reservoir = await self.objects.get(ReservoirModel, slug=self.slug)

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
                instance = Situation.parse_obj(normalized_values)
            except ValidationError as error:
                logging.error(f'{reservoir.slug}: {repr(error)}')
            else:
                result.append(instance)
        logging.info(f'{self.__class__.__name__} stop parsing')
        return result


class GismeteoParser(AbstractParser):
    base_url: str = environ.get(
        'GIS_URL', 'https://api.gismeteo.net/v2/weather/forecast'
    )

    def __init__(self, objects):
        self.objects = objects

    async def get_date(self) -> dt.date:
        return dt.date.today()

    async def get_url(self, geo_object: GeoObjectModel) -> str:
        return f'{self.base_url}/{geo_object.gismeteo_id}'

    async def get_page(
        self, session: ClientSession, geo_object: GeoObjectModel
    ) -> Dict:
        url = await self.get_url(geo_object)
        async with session.get(url=url, params={'days': 3}) as r:
            return await r.json()

    async def parsing(self, page: Dict) -> List[Gismeteo]:
        logging.info(f'{self.__class__.__name__} start parsing')
        instances = parse_obj_as(List[Gismeteo], page['response'])
        logging.info(f'{self.__class__.__name__} stop parsing')
        return instances

    async def worker(self):
        headers = {
            'X-Gismeteo-Token': environ['GIS_TOKEN'],
            'Accept-Encoding': 'gzip',
        }
        async with ClientSession(headers=headers) as session:
            geo_objects = await self.objects.execute(
                GeoObjectModel.select().where(GeoObjectModel.gismeteo_id != None)
            )
            for geo_object in geo_objects:
                try:
                    page = await self.get_page(session, geo_object)
                    if page['meta']['code'] != '200':
                        logging.error(page['meta']['message'])
                        continue
                    instances = await self.parsing(page)
                    await self.save(instances, geo_object)
                except (ValueError, AttributeError, ValidationError) as error:
                    logging.error(repr(error))
            await asyncio.sleep(1)

    async def save(self, instances: List[Gismeteo], geo_object: GeoObjectModel):
        saved_count = 0
        for instance in instances:
            instance.geo_object_id = geo_object.id
            obj, created = await self.objects.get_or_create(
                WeatherModel,
                date=instance.date,
                geo_object_id=geo_object.id,
                defaults=instance.dict(),
            )
            if not created:
                await self.objects.execute(
                    WeatherModel.update(
                        instance.dict()
                    ).where(
                        WeatherModel.id==obj.id
                    )
                )
            saved_count += created
        logging.info(f'{self.__class__.__name__} saved {saved_count} new records')
