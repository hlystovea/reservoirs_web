import datetime as dt
import time
from abc import ABCMeta, abstractmethod
from os import environ as env
from typing import Optional

import httpx
from celery.utils.log import get_task_logger
from django.db import DatabaseError
from django.db.models import Max, manager
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from reservoirs.models import Reservoir, WaterSituation
from services.parsers import (AbstractParser, Forecast, KrasParser,
                              RP5Parser, RushydroParser, Situation)
from weather.models import GeoObject, Weather

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
    base_url = env.get(
        'RUSHYDRO_URL', 'http://www.rushydro.ru/hydrology/informer'
    )

    @classmethod
    def get_date(cls):
        try:
            last_date = WaterSituation.objects.exclude(
                reservoir__slug='kras'
            ).values(
                'reservoir'
            ).annotate(
                last_date=Max('date')
            ).earliest(
                'last_date'
            )['last_date']
            return last_date + dt.timedelta(days=1)

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

            logger.info(f'{cls.__name__} saved {saved_count} new objs')

            date += dt.timedelta(days=1)

        logger.info(f'{cls.__name__} stop scraping')


class KrasScraper(SituationMixin):
    first_date = dt.date(2021, 7, 1)
    parser = KrasParser()
    base_url = env.get('KRAS_URL', 'https://enbvu.ru/i03_deyatelnost')
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
            last_situation = WaterSituation.objects.filter(
                reservoir__slug=cls.slug).latest('date')
            return last_situation.date + dt.timedelta(days=1)

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


class RP5Scraper(AbstractParser):
    first_date = dt.date(2005, 2, 1)
    parser = RP5Parser()
    base_url = env.get('RP5_URL', 'https://rp5.ru/Архив_погоды_в_Бее')

    @staticmethod
    def get_driver() -> WebDriver:
        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')
        selenium_url = env.get('SELENIUM_URL', 'http://selenium:4444/wd/hub')
        return webdriver.Remote(selenium_url, options=options)

    @classmethod
    def get_objects(cls) -> manager.BaseManager[GeoObject]:
        return GeoObject.objects.filter(station_id__isnull=False).all()

    @classmethod
    def get_last_date(cls, geo_object):
        try:
            last_observed_weather = Weather.objects.filter(
                geo_object=geo_object,
                is_observable=True
            ).latest(
                'date'
            )
            return last_observed_weather.date.date()

        except Weather.DoesNotExist:
            return cls.first_date

    @classmethod
    def get_url(cls) -> str:
        return cls.base_url

    @classmethod
    def load_geo_object_page(cls, driver: WebDriver, geo_object: GeoObject):
        station_id_input_element = driver.find_element(By.ID, 'wmo_id')

        station_id_input_element.clear()
        station_id_input_element.send_keys(geo_object.station_id)
        time.sleep(3)

        station_id_input_element.send_keys(Keys.ENTER)
        time.sleep(3)

    @classmethod
    def get_page(cls, driver: WebDriver, date: dt.date) -> str:
        date_picker = driver.find_element(By.ID, 'calender_archive')
        date_button = driver.find_element(By.CLASS_NAME, 'archButton')

        date_picker.clear()
        date_picker.send_keys(date.strftime('%d.%m.%Y'))

        date_button.click()

        return driver.page_source

    @classmethod
    def save(
            cls, forecast: Forecast, geo_object: GeoObject
            ) -> tuple[Optional[Weather], bool]:
        try:
            obj, created = Weather.objects.update_or_create(
                date=forecast.date,
                geo_object=geo_object,
                defaults=forecast.dict()
            )
            return obj, created

        except DatabaseError as error:
            logger.error(f'{cls.__name__} {repr(error)}')
            return None, False

    @classmethod
    def scrape(cls):
        logger.info(f'{cls.__name__} start scraping')

        geo_objects = cls.get_objects()
        logger.info(f'Get {len(geo_objects)} geo objects')

        driver = cls.get_driver()

        try:
            driver.get(cls.base_url)

            for geo_object in geo_objects:
                cls.load_geo_object_page(driver, geo_object)
                logger.info(f'Get page for {geo_object}')

                last_date = cls.get_last_date(geo_object)
                logger.info(f'Last date: {last_date}')

                while last_date <= dt.date.today():
                    saved_count = 0

                    page = cls.get_page(driver, last_date)
                    forecasts = cls.parser.parse(page)

                    for forecast in forecasts:
                        _, saved = cls.save(forecast, geo_object)
                        saved_count += saved

                    logger.info(f'{cls.__name__} saved {saved_count} new objs')

                    last_date += dt.timedelta(days=1)

        except WebDriverException as error:
            logger.error(f'Some error occured: {error!r}')

        finally:
            driver.close()

        logger.info(f'{cls.__name__} stop scraping')
