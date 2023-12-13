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
from services.schemes import (Gismeteo, Roshydromet, RP5,
                              RushydroSituation, Situation)
from services.utils import parser_info

logger = get_task_logger(__name__)


class AbstractParser(metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def parse(cls, *args, **kwargs):
        pass


class RushydroParser(AbstractParser):
    params = {
        'date': 'water-date',
        'level': 'water-level',
        'free_capacity': 'water-polemk',
        'inflow': 'water-pritok',
        'outflow': 'water-rashod',
        'spillway': 'water-sbros',
    }

    @classmethod
    def get_values(cls, data: Union[Tag, NavigableString]) -> Iterable:
        return zip(*(data[i].split(',')[::-1] for i in cls.params.values()))

    @classmethod
    def preprocessing(cls, values: Iterable) -> list[dict]:
        return [dict(zip(cls.params.keys(), i)) for i in values]

    @classmethod
    def parse(cls, page: str, reservoir: Reservoir) -> list[RushydroSituation]:
        soup = BeautifulSoup(page, 'html.parser')
        situations = []

        try:
            options = soup.find('select', id="ges")
            option = options.find('option', string=reservoir.station_name)

            logger.info(f'{cls.__name__} parsed {reservoir.name}')

            if option:
                data = cls.preprocessing(cls.get_values(option))
                situations = parse_obj_as(list[RushydroSituation], data)

        except (ValueError, AttributeError, ValidationError, KeyError) as e:
            logger.error(f'{cls.__name__} {repr(e)}')

        finally:
            return situations


class KrasParser(AbstractParser):
    @staticmethod
    def get_values(raw_data: Union[Tag, NavigableString]) -> tuple:
        level_str = raw_data.find_all(string=re.compile('верхний бьеф'))[2]
        inflow_str = raw_data.find_all(string=re.compile('приток общий'))[0]
        spillway_str = raw_data.find_all(string=re.compile('холостой сброс'))[2]  # noqa(E501)

        level = re.findall(r'[0-9]+[,.][0-9]+', level_str)[0]
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


class SayanParser(KrasParser):
    @staticmethod
    def get_values(raw_data: Union[Tag, NavigableString]) -> tuple:
        level_str = raw_data.find_all(string=re.compile('верхний бьеф'))[0]
        inflow_str = raw_data.find_all(string=re.compile('приток'))[0]
        spillway_str = raw_data.find_all(string=re.compile('холостой сброс'))[0]  # noqa(E501)

        level = re.findall(r'[0-9]+[,.][0-9]+', level_str)[0]
        outflow = re.findall(r'[0-9]+', level_str)[-1]
        inflow = re.findall(r'[0-9]+', inflow_str)[0]
        spillway = re.findall(r'[0-9]+', spillway_str)[0]

        return level, inflow, outflow, spillway


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
    def get_observations(cls, table: Union[Tag, NavigableString]) -> list[dict]:  # noqa(E501)
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
    def parse(cls, page: str) -> list[RP5]:
        soup = BeautifulSoup(page, 'html.parser')
        archive_table = soup.find('table', id='archiveTable')

        if not archive_table:
            logger.error(f'{cls.__name__} no content')
            return []

        try:
            observations = cls.get_observations(archive_table)
            return parse_obj_as(list[RP5], observations)

        except (AttributeError, ValidationError, IndexError) as error:
            logger.error(f'{cls.__name__} {repr(error)}')
            return []


class GismeteoParser(AbstractParser):
    @classmethod
    def parse(cls, data: dict) -> list[Gismeteo]:
        try:
            return parse_obj_as(list[Gismeteo], data['response'])
        except (KeyError, ValidationError) as error:
            logger.error(f'{cls.__name__} {repr(error)}')
            return []


class RoshydrometParser(AbstractParser):
    @staticmethod
    def get_values(row: Tag) -> list:
        return re.findall(r'сегодня?|-?[0-9]+|штиль?', row.text, re.I)[-5:]

    @classmethod
    def get_observations(cls, table: Union[Tag, NavigableString]) -> list[dict]:  # noqa(E501)
        keys = (
            'temp',
            'pressure',
            'precipitation',
            'cloudiness',
            'wind_speed',
            'date',
        )
        hours = {
            'ночью': 1,
            'днем': 13,
        }

        date = dt.date.today()
        forecasts = []

        for row in table.find_all('tr'):
            date_str = row.find('div', **{'class': 'date'})

            if date_str and date_str.text != 'Сегодня':
                date = parse_date(date_str.text, parserinfo=parser_info)

            time = row.find('div', **{'class': 'small'}).text
            datetime = dt.datetime.combine(date, dt.time(hours.get(time, 0)))

            values = cls.get_values(row)
            values.append(datetime)

            forecasts.append(dict(zip(keys, values)))

        return forecasts

    @classmethod
    def parse(cls, page: str) -> list[Roshydromet]:
        soup = BeautifulSoup(page, 'html.parser')
        forecast_table = soup.find('tbody')

        if not forecast_table:
            logger.error(f'{cls.__name__} no content')
            return []

        try:
            forecasts = cls.get_observations(forecast_table)
            return parse_obj_as(list[Roshydromet], forecasts)

        except (AttributeError, ValidationError, IndexError) as error:
            logger.error(f'{cls.__name__} {repr(error)}')
            return []
