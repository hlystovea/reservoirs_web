import re
import datetime as dt
from abc import ABCMeta, abstractmethod
from typing import Iterable, Optional, Union

from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag
from celery.utils.log import get_task_logger
from dateutil.parser import parse as parse_date
from pydantic import parse_obj_as, ValidationError

from reservoirs.models import Reservoir
from services.schemes import Forecast, Situation
from services.utils import parser_info

logger = get_task_logger(__name__)


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

            return Situation(date=date, **normalized_values)

        except (ValueError, AttributeError, ValidationError) as error:
            logger.error(f'{cls.__name__} {repr(error)}')


class RP5Parser(AbstractParser):
    @staticmethod
    def get_headlines(first_row: Union[Tag, NavigableString]) -> list[str]:
        return [cell.text for cell in first_row.find_all('td')]

    @staticmethod
    def get_values(row: Tag) -> list[Optional[str]]:
        values = []

        for cell in row.find_all('td'):
            if cell.find('div'):
                values.append(cell.find('div').text)
            else:
                values.append(cell.text)

        return values

    @classmethod
    def preprocessing(cls, headlines: list, row: Tag) -> dict:
        return dict(zip(headlines[::-1], cls.get_values(row)[::-1]))

    @classmethod
    def get_observations(cls, table: Union[Tag, NavigableString]) -> list[dict]:
        date_str = table.find('td', **{'class_': 'cl_dt'})
        date = parse_date(date_str.text, parserinfo=parser_info)

        logger.info(f'{cls.__name__} parsed date {date.date()}')

        headlines = cls.get_headlines(table.find('tr'))
        observations = []
        last_hour = 24

        for row in table.find('tbody').contents[1:]:
            hours = int(row.find('div', **{'class_': 'dfs'}).text)

            if hours > last_hour:
                break

            observation = cls.preprocessing(headlines, row)
            observation['date'] = date + dt.timedelta(hours=hours)
            observations.append(observation)

            last_hour = hours

        return observations

    @classmethod
    def parse(cls, page: str) -> list[Forecast]:
        soup = BeautifulSoup(page, 'html.parser')
        archive_table = soup.find('table', id='archiveTable')

        if not archive_table:
            logger.error(f'{cls.__name__} no content')
            return []

        try:
            observations = cls.get_observations(archive_table)
            return parse_obj_as(list[Forecast], observations)

        except (AttributeError, ValidationError, IndexError) as error:
            logger.error(f'{cls.__name__} {repr(error)}')
            return []
