import re
import datetime as dt
from abc import ABCMeta, abstractmethod
from os import environ
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from bs4.element import ResultSet
from celery.utils.log import get_task_logger
from django.db import DatabaseError
from django.db.models import Max
from pydantic import BaseModel, parse_obj_as, root_validator, ValidationError

from reservoirs.models import Reservoir, WaterSituation
from weather.models import GeoObject, Weather

logger = get_task_logger(__name__)


class Situation(BaseModel):
    level: float
    free_capacity: Optional[int]
    inflow: Optional[int]
    outflow: Optional[int]
    spillway: Optional[int]

    class Config:
        orm_mode = True

    @root_validator(pre=True)
    def check_fields(cls, values):
        for key, value in values.items():
            if isinstance(value, str) and 'нет' in value:
                values[key] = None
        return values


class WeatherSchema(BaseModel):
    date: dt.datetime
    geo_object_id: Optional[int]
    temp: float
    pressure: int
    humidity: int
    cloudiness: int
    wind_speed: float
    wind_direction: int
    precipitation: float
    is_observable: bool

    class Config:
        orm_mode = True


class GismeteoSchema(WeatherSchema):
    def __init__(self, **kwargs):
        kwargs['temp'] = kwargs['temperature']['air']['C']
        kwargs['pressure'] = kwargs['pressure']['mm_hg_atm']
        kwargs['humidity'] = kwargs['humidity']['percent']
        kwargs['cloudiness'] = kwargs['cloudiness']['percent']
        kwargs['wind_speed'] = kwargs['wind']['speed']['m_s']
        kwargs['wind_direction'] = kwargs['wind']['direction']['scale_8']
        kwargs['precipitation'] = kwargs['precipitation']['amount'] or 0
        kwargs['is_observable'] = True if kwargs['kind'] == 'Obs' else False
        kwargs['date'] = dt.datetime.strptime(
            kwargs['date']['UTC'], '%Y-%m-%d %H:%M:%S'
        )
        super().__init__(**kwargs)


class AbstractParser(metaclass=ABCMeta):
    base_url: str

    @abstractmethod
    def get_date(self) -> dt.date:
        pass

    @abstractmethod
    def get_url(self, *args, **kwargs) -> str:
        pass

    @abstractmethod
    def get_page(self) -> str:
        pass

    @abstractmethod
    def parsing(self, *args, **kwargs):
        pass

    @abstractmethod
    def worker(self):
        pass


class SituationMixin(AbstractParser):
    first_date: dt.date = dt.date(2013, 4, 13)

    def get_page(self, date: dt.date) -> str:
        url = self.get_url(date)
        response = httpx.get(url=url)
        if response.is_error:
            raise httpx.HTTPError(
                f'{response.status_code} {response.reason_phrase}'
            )
        return response.text

    def worker(self):
        date = self.get_date()
        while date <= date.today():
            try:
                page = self.get_page(date=date)
                self.parsing(page, date=date)
            except (ValueError, AttributeError) as error:
                logger.error(repr(error))
            date += dt.timedelta(days=1)


class RushydroParser(SituationMixin):
    base_url: str = environ.get(
        'RUSHYDRO_URL', 'http://www.rushydro.ru/hydrology/informer'
    )

    def get_date(self):
        try:
            return WaterSituation.objects.exclude(reservoir__slug='kras') \
                                 .values('reservoir') \
                                 .annotate(last_date=Max('date')) \
                                 .earliest('last_date')['last_date']
        except WaterSituation.DoesNotExist:
            return self.first_date

    def get_url(self, date: dt.date) -> str:
        return f'{self.base_url}/?date={date.isoformat()}'

    def preprocessing(self, values: ResultSet) -> dict:
        keys = ['level', 'free_capacity', 'inflow', 'outflow', 'spillway']
        values = [v.text.split()[0].split('м')[0] for v in values]
        return dict(zip(keys, values))

    def parsing(self, page: str, **kwargs):
        logger.info(f'{self.__class__.__name__} start parsing')

        soup = BeautifulSoup(page, 'html.parser')
        date_str = soup.find('input', id='popupDatepicker').get('value')
        date = dt.datetime.strptime(date_str, '%d.%m.%Y').date()

        logger.info(f'{self.__class__.__name__} parsed date - {date}')

        saved_count = 0

        for reservoir in Reservoir.objects.all():
            informer_data = soup.find(
                'div',
                class_=f'informer-block {reservoir.slug}',
            )

            if informer_data is None:
                continue

            num_values = informer_data.find_all('b')
            normalized_values = self.preprocessing(num_values[3:])

            try:
                cleaned_data = Situation(**normalized_values).dict()

                _, created = WaterSituation.objects.get_or_create(
                    date=date,
                    reservoir=reservoir,
                    defaults=cleaned_data
                )

                saved_count += created

            except (DatabaseError, ValidationError) as error:
                logger.error(f'{self.__class__.__name__} {repr(error)}')

        logger.info(f'{self.__class__.__name__} saved {saved_count} new objs')
        logger.info(f'{self.__class__.__name__} stop parsing')


class KrasParser(SituationMixin):
    slug: str = 'kras'
    first_date: dt.date = dt.date(2021, 7, 1)
    base_url: str = environ.get('KRAS_URL', 'https://enbvu.ru/i03_deyatelnost')

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

    def get_date(self):
        try:
            latest_situation = WaterSituation.objects.filter(
                reservoir__slug='kras').latest('date')
            return latest_situation.date
        except WaterSituation.DoesNotExist:
            return self.first_date

    def get_url(self, date: dt.date) -> str:
        num_year = date.year - self.first_date.year
        num_month = date.month - self.first_date.month
        page_number = num_year * 12 + num_month + 1

        return self.base_url + '/i03.07.{0:=02}_{1}.php'.format(
            page_number, self.month_names[date.month]
        )

    def preprocessing(self, values: list[ResultSet]) -> dict:
        keys = ['level', 'inflow', 'outflow', 'spillway']
        values = [float(v.replace(",", ".")) for v in values]
        return dict(zip(keys, values))

    def parsing(self, page: str, date: dt.date):
        logger.info(f'{self.__class__.__name__} start parsing')

        soup = BeautifulSoup(page, 'html.parser')
        iul_class = soup.find_all('div', class_='iul_day_1')
        reservoir = Reservoir.objects.get(slug=self.slug)

        saved_count = 0

        for block in iul_class:

            if not block.find('div', class_='date'):
                continue

            parsed_date = dt.date(
                year=date.year,
                month=date.month,
                day=int(block.get('id').split('_')[-1])
            )

            logger.info(f'{self.__class__.__name__} parsed date {parsed_date}')  # noqa(E501)

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
            normalized_values = self.preprocessing(num_values)

            try:
                cleaned_data = Situation(**normalized_values).dict()

                _, created = WaterSituation.objects.get_or_create(
                    date=parsed_date,
                    reservoir=reservoir,
                    defaults=cleaned_data
                )

                saved_count += created

            except (DatabaseError, ValidationError) as error:
                logger.error(f'{self.__class__.__name__} {repr(error)}')

        logger.info(f'{self.__class__.__name__} saved {saved_count} new objs')
        logger.info(f'{self.__class__.__name__} stop parsing')


class GismeteoParser(AbstractParser):
    base_url: str = environ.get(
        'GIS_URL', 'https://api.gismeteo.net/v2/weather/forecast'
    )

    def get_date(self) -> dt.date:
        return dt.date.today()

    def get_url(self, geo_object: GeoObject) -> str:
        return f'{self.base_url}/{geo_object.gismeteo_id}'

    def get_page(self, geo_object: GeoObject) -> httpx.Response:
        headers = {
            'X-Gismeteo-Token': environ['GIS_TOKEN'],
            'Accept-Encoding': 'gzip',
        }
        url = self.get_url(geo_object)
        return httpx.get(url=url, headers=headers, params={'days': 3})

    def parsing(self, geo_object: GeoObject, data: dict):
        logger.info(f'{self.__class__.__name__} start parsing')

        forecasts = parse_obj_as(list[GismeteoSchema], data['response'])

        saved_count = 0

        for forecast in forecasts:
            _, created = Weather.objects.update_or_create(
                date=forecast.date,
                geo_object_id=geo_object.pk,
                defaults=forecast.dict(exclude={'date', 'geo_object_id'}),
            )

            saved_count += created

        logger.info(f'{self.__class__.__name__} saved {saved_count} new records')  # noqa (501)
        logger.info(f'{self.__class__.__name__} stop parsing')

    def worker(self):
        geo_objects = GeoObject.objects.filter(gismeteo_id__isnull=False)

        for geo_object in geo_objects:
            try:
                response = self.get_page(geo_object)

                if response.status_code != httpx.codes.OK:
                    logger.error(f'HTTPError: status={response.status_code}')
                    continue

                self.parsing(geo_object, response.json())

            except (ValueError, AttributeError, ValidationError) as error:
                logger.error(repr(error))
