import logging
import datetime as dt
from abc import ABCMeta, abstractmethod
from logging.handlers import RotatingFileHandler
from os import environ
from typing import Dict, List

from bs4 import BeautifulSoup
from bs4.element import ResultSet
from pydantic import ValidationError

from db.schemas import Reservoir, WaterSituation


rotate_file_handler = RotatingFileHandler('logs/parsing.log', 5000000, 2)
console_out_hundler = logging.StreamHandler()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(funcName)s: %(message)s',
    handlers=[rotate_file_handler, console_out_hundler],
)


class AbstractParser(metaclass=ABCMeta):
    slug: str
    base_url: str
    last_date: dt.date

    @abstractmethod
    def get_url(self) -> str:
        pass

    @abstractmethod
    def preprocessing(self) -> Dict:
        pass

    @abstractmethod
    def parsing(self):
        pass


class RushydroParser(AbstractParser):
    slug: str = 'sayano'
    last_date: dt.date = dt.date(2013, 4, 13)
    base_url: str = environ.get(
        'RUSHYDRO_URL', 'http://www.rushydro.ru/hydrology/informer'
    )

    async def get_url(self, **kwargs) -> str:
        if 'date' in kwargs:
            return f'{self.base_url}/?date={kwargs["date"].isoformat()}'
        return self.base_url

    async def preprocessing(self, values: ResultSet) -> Dict:
        keys = ['level', 'free_capacity', 'inflow', 'outflow', 'spillway']
        values = [v.text.split()[0].split('м')[0] for v in values]
        return dict(zip(keys, values))

    async def parsing(
        self, page: str, reservoirs: List[Reservoir]
    ) -> List[WaterSituation]:
        logging.info('start parsing')
        soup = BeautifulSoup(page, 'html.parser')
        date_str = soup.find('input', id='popupDatepicker').get('value')
        date = dt.datetime.strptime(date_str, '%d.%m.%Y').date()
        logging.info(f'parsed date - {date}')
        result = []

        for reservoir in reservoirs:
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
        logging.info('stop parsing')
        return result
