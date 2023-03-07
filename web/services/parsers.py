import re
import datetime as dt
from abc import ABCMeta, abstractmethod
from typing import Iterable, Optional, Union

from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag
from celery.utils.log import get_task_logger
from pydantic import BaseModel, root_validator, ValidationError

from reservoirs.models import Reservoir

logger = get_task_logger(__name__)


class Situation(BaseModel):
    date: Optional[dt.date]
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


class AbstractParser(metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def parse(cls, *args, **kwargs):
        pass


class RushydroParser(AbstractParser):
    @staticmethod
    def get_values(raw_data: Union[Tag, NavigableString]) -> list:
        return raw_data.find_all('b')[3:]

    @staticmethod
    def preprocessing(values: Iterable) -> dict:
        keys = ('level', 'free_capacity', 'inflow', 'outflow', 'spillway')
        normalized_values = (v.text.split()[0].split('м')[0] for v in values)
        return dict(zip(keys, normalized_values))

    @classmethod
    def parse(cls, page: str, reservoir: Reservoir) -> Optional[Situation]:
        soup = BeautifulSoup(page, 'html.parser')

        try:
            date_str = soup.find('input', id='popupDatepicker').get('value')
            date = dt.datetime.strptime(date_str, '%d.%m.%Y').date()

            logger.info(
                f'{cls.__name__} parsed date {date:%Y-%m-%d}, {reservoir.name}'
            )

            raw_data = soup.find(
                'div',
                class_=f'informer-block {reservoir.slug}',
            )

            if raw_data:
                normalized_values = cls.preprocessing(cls.get_values(raw_data))

                return Situation(date=date, **normalized_values)

        except (ValueError, AttributeError, ValidationError) as error:
            logger.error(f'{cls.__name__} {repr(error)}')


class KrasParser(AbstractParser):
    @staticmethod
    def get_values(raw_data: Union[Tag, NavigableString]) -> tuple:

        level_str = raw_data.find_all(string=re.compile('верхний бьеф'))[2]
        inflow_str = raw_data.find_all(string=re.compile('приток общий'))[0]
        spillway_str = raw_data.find_all(string=re.compile('холостой сброс'))[2]  # noqa(E501)

        level = re.findall(r'[0-9]+,[0-9]+', level_str)[0]
        outflow = re.findall(r'[0-9]+', level_str)[-1]
        inflow = re.findall(r'[0-9]+', inflow_str)[0]
        spillway = re.findall(r'[0-9]+', spillway_str)[0]

        return level, inflow, outflow, spillway

    @staticmethod
    def preprocessing(values: Iterable) -> dict:
        keys = ('level', 'inflow', 'outflow', 'spillway')
        normalized_values = (float(v.replace(",", ".")) for v in values)
        return dict(zip(keys, normalized_values))

    @classmethod
    def parse(cls, page: str, date: dt.date) -> Optional[Situation]:
        soup = BeautifulSoup(page, 'html.parser')

        try:
            id_ = f'iul_day_{date.day}'
            raw_data = soup.find('div', class_='iul_day_1', id=id_)

            logger.info(f'{cls.__name__} parsed date {date}')

            if raw_data is None:
                logger.warning(f'{cls.__name__} Incorrect id: {id_}')
                return

            if raw_data.find(string=re.compile('Нет данных')):
                logger.info(f'{cls.__name__} No data')
                return

            normalized_values = cls.preprocessing(cls.get_values(raw_data))

            return Situation(**normalized_values)

        except (ValueError, AttributeError, ValidationError) as error:
            logger.error(f'{cls.__name__} {repr(error)}')
