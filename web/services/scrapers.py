import datetime as dt
from abc import ABCMeta, abstractmethod
from os import environ
from typing import Optional

import httpx
from celery.utils.log import get_task_logger
from django.db import DatabaseError
from django.db.models import Max

from reservoirs.models import Reservoir, WaterSituation
from services.parsers import (AbstractParser, KrasParser,
                              RushydroParser, Situation)

logger = get_task_logger(__name__)


class AbstractScraper(metaclass=ABCMeta):
    first_date: dt.date
    parser: AbstractParser
    base_url: str

    @classmethod
    @abstractmethod
    def get_date(cls) -> dt.date:
        pass

    @classmethod
    @abstractmethod
    def get_url(cls, *args, **kwargs) -> str:
        pass

    @classmethod
    @abstractmethod
    def scrape(cls):
        pass


class SituationMixin(AbstractScraper):
    @classmethod
    def get_page(cls, date: dt.date) -> str:
        url = cls.get_url(date)
        response = httpx.get(url=url)

        if response.is_error:
            raise httpx.HTTPError(
                f'{response.status_code} {response.reason_phrase}')

        return response.text

    @classmethod
    def save(
            cls, date: dt.date, situation: Situation, reservoir: Reservoir
            ) -> tuple[Optional[WaterSituation], bool]:
        try:
            obj, created = WaterSituation.objects.get_or_create(
                date=date,
                reservoir=reservoir,
                defaults=situation.dict()
            )
            return obj, created

        except DatabaseError as error:
            logger.error(f'{cls.__name__} {repr(error)}')

            return None, False


class RushydroScraper(SituationMixin):
    first_date = dt.date(2013, 4, 13)
    parser = RushydroParser()
    base_url = environ.get(
        'RUSHYDRO_URL', 'http://www.rushydro.ru/hydrology/informer'
    )

    @classmethod
    def get_date(cls):
        try:
            return WaterSituation.objects.exclude(reservoir__slug='kras') \
                                 .values('reservoir') \
                                 .annotate(last_date=Max('date')) \
                                 .earliest('last_date')['last_date']
        except WaterSituation.DoesNotExist:
            return cls.first_date

    @classmethod
    def get_url(cls, date: dt.date) -> str:
        return f'{cls.base_url}/?date={date.isoformat()}'

    @classmethod
    def scrape(cls):
        logger.info(f'{cls.__name__} start scraping')

        date = cls.get_date()
        reservoirs = Reservoir.objects.exclude(slug='kras').all()

        while date <= date.today():
            page = cls.get_page(date=date)
            saved_count = 0

            for reservoir in reservoirs:
                situation = cls.parser.parse(page, reservoir)

                if situation:
                    _, saved = cls.save(situation.date, situation, reservoir)
                    saved_count += saved

            logger.info(
                f'{cls.__name__} saved {saved_count} new objs')

            date += dt.timedelta(days=1)

        logger.info(f'{cls.__name__} stop scraping')


class KrasScraper(SituationMixin):
    first_date = dt.date(2021, 7, 1)
    parser = KrasParser()
    base_url = environ.get('KRAS_URL', 'https://enbvu.ru/i03_deyatelnost')
    slug: str = 'kras'
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

    @classmethod
    def get_date(cls):
        try:
            latest_situation = WaterSituation.objects.filter(
                reservoir__slug=cls.slug).latest('date')
            return latest_situation.date
        except WaterSituation.DoesNotExist:
            return cls.first_date

    @classmethod
    def get_url(cls, date: dt.date) -> str:
        num_year = date.year - cls.first_date.year
        num_month = date.month - cls.first_date.month
        page_number = num_year * 12 + num_month + 1

        return cls.base_url + '/i03.07.{0:=02}_{1}.php'.format(
            page_number, cls.month_names[date.month]
        )

    @classmethod
    def scrape(cls):
        logger.info(f'{cls.__name__} start scraping')
        reservoir = Reservoir.objects.get(slug=cls.slug)

        date = cls.get_date()

        while date <= date.today():
            page = cls.get_page(date=date)
            situation = cls.parser.parse(page, date)

            if situation:
                obj, saved = cls.save(date, situation, reservoir)

                if saved:
                    logger.info(f'{cls.__name__} saved new obj: {obj}')

            date += dt.timedelta(days=1)

        logger.info(f'{cls.__name__} stop scraping')
