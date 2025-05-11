import datetime as dt
import time
from abc import ABCMeta, abstractmethod
from os import environ as env
from typing import Optional

import httpx
from celery.utils.log import get_task_logger
from django.db import DatabaseError
from django.db.models import manager
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from reservoirs.models import Reservoir, WaterSituation
from services.parsers import (AbstractParser, GismeteoParser,
                              RoshydrometParser, RP5Parser,
                              RushydroParser, Situation)
from services.schemes import WeatherBase
from weather.models import GeoObject, Weather

logger = get_task_logger(__name__)


class AbstractScraper(metaclass=ABCMeta):
    parser: AbstractParser
    base_url: str

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
    def get_page(cls, *args, **kwargs) -> str:
        url = cls.get_url(*args, **kwargs)

        with httpx.Client() as client:
            response = client.get(url, follow_redirects=True)

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
    parser = RushydroParser()
    base_url = env.get(
        'RUSHYDRO_URL', 'https://www.rushydro.ru/informer/'
    )

    @staticmethod
    def get_driver() -> WebDriver:
        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')
        options.add_argument("--enable-javascript")
        selenium_url = env.get('SELENIUM_URL', 'http://selenium:4444/wd/hub')
        return webdriver.Remote(selenium_url, options=options)

    @classmethod
    def get_page(cls, driver: WebDriver) -> str:
        driver.get(cls.get_url())
        time.sleep(3)
        return driver.page_source

    @classmethod
    def get_url(cls, *args, **kwargs) -> str:
        return cls.base_url

    @classmethod
    def scrape(cls):
        logger.info(f'{cls.__name__} start scraping')

        reservoirs = Reservoir.objects.filter(
            station_name__isnull=False
        ).exclude(
            slug='kras'
        ).all()

        saved_count = 0
        driver = cls.get_driver()

        try:
            page = cls.get_page(driver)

            for reservoir in reservoirs:
                situations = cls.parser.parse(page, reservoir)

                for situation in situations:
                    _, saved = cls.save(situation.date, situation, reservoir)
                    saved_count += saved

        except WebDriverException as error:
            logger.error(f'Some error occured: {error!r}')

        finally:
            driver.quit()

        logger.info(f'{cls.__name__} saved {saved_count} new objs')
        logger.info(f'{cls.__name__} stop scraping')


class EbvuScraper(SituationMixin):
    first_date = dt.date(2021, 7, 1)
    base_url = env.get('EBVU_URL', 'https://enbvu.ru/i03_deyatelnost')
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

    def __init__(self, parser: AbstractParser, reservoir_slug: str):
        self.parser = parser
        self.slug = reservoir_slug

    def get_date(self):
        try:
            last_situation = WaterSituation.objects.filter(
                reservoir__slug=self.slug).latest('date')
            return last_situation.date + dt.timedelta(days=1)

        except WaterSituation.DoesNotExist:
            return self.first_date

    @classmethod
    def get_url(cls, date: dt.date) -> str:
        num_year = date.year - cls.first_date.year
        num_month = date.month - cls.first_date.month
        page_number = num_year * 12 + num_month + 1

        return cls.base_url + '/i03.07.{0:=02}_{1}.php'.format(
            page_number, cls.month_names[date.month]
        )

    def scrape(self):
        logger.info(f'{self.__class__.__name__} start scraping')
        reservoir = Reservoir.objects.get(slug=self.slug)

        date = self.get_date()

        while date <= date.today():
            page = self.get_page(date=date)
            situation = self.parser.parse(page, date)

            if situation:
                obj, saved = self.save(date, situation, reservoir)

                if saved:
                    logger.info(
                        f'{self.__class__.__name__} saved new obj: {obj}'
                    )

            date += dt.timedelta(days=1)

        logger.info(f'{self.__class__.__name__} stop scraping')


class RP5Scraper(AbstractScraper):
    first_date: dt.date = dt.date(2005, 2, 1)
    parser: RP5Parser = RP5Parser()
    base_url: str = env.get('RP5_URL', 'https://rp5.ru/Архив_погоды_в_Бее')

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
        cls, forecast: WeatherBase, geo_object: GeoObject
    ) -> tuple[Optional[Weather], bool]:
        try:
            obj, created = Weather.objects.update_or_create(
                date=forecast.date,
                geo_object=geo_object,
                is_observable=True,
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
            driver.quit()

        logger.info(f'{cls.__name__} stop scraping')


class GismeteoScraper(AbstractScraper):
    parser: GismeteoParser = GismeteoParser()
    base_url: str = env.get(
        'GIS_URL', 'https://api.gismeteo.net/v2/weather/forecast'
    )

    @classmethod
    def get_objects(cls) -> manager.BaseManager[GeoObject]:
        return GeoObject.objects.filter(gismeteo_id__isnull=False).all()

    @classmethod
    def get_url(cls, geo_object: GeoObject) -> str:
        return f'{cls.base_url}/{geo_object.gismeteo_id}/'

    @classmethod
    def get_data(cls, geo_object: GeoObject) -> dict:
        url = cls.get_url(geo_object)
        params = {
            'days': 10,
        }
        headers = {
            'X-Gismeteo-Token': env['GIS_TOKEN'],
            'Accept-Encoding': 'gzip',
        }

        response = httpx.get(url=url, params=params, headers=headers)

        if response.is_error:
            raise httpx.HTTPError(
                f'{response.status_code} {response.reason_phrase}')

        return response.json()

    @classmethod
    def save(
            cls, forecast: WeatherBase, geo_object: GeoObject
            ) -> tuple[Optional[Weather], bool]:
        try:
            obj, created = Weather.objects.update_or_create(
                date=forecast.date,
                geo_object=geo_object,
                is_observable=False,
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

        saved_count = 0

        for geo_object in geo_objects:
            try:
                data = cls.get_data(geo_object)
                forecasts = cls.parser.parse(data)

                for forecast in forecasts:
                    _, saved = cls.save(forecast, geo_object)
                    saved_count += saved

            except httpx.HTTPError as error:
                logger.error(f'Some error occured: {error!r}')

        logger.info(f'{cls.__name__} saved {saved_count} new objs')
        logger.info(f'{cls.__name__} stop scraping')


class RoshydrometScraper(GismeteoScraper):
    parser: RoshydrometParser = RoshydrometParser()
    base_url: str = env.get(
        'ROSHYDROMET_URL', 'https://www.meteorf.gov.ru/product/weather'
    )

    @classmethod
    def get_objects(cls) -> manager.BaseManager[GeoObject]:
        return GeoObject.objects.filter(roshydromet_id__isnull=False).all()

    @classmethod
    def get_url(cls, geo_object: GeoObject) -> str:
        return f'{cls.base_url}/{geo_object.roshydromet_id}/'

    @classmethod
    def get_data(cls, geo_object: GeoObject) -> str:
        url = cls.get_url(geo_object)

        response = httpx.get(url=url, verify=False)

        if response.is_error:
            raise httpx.HTTPError(
                f'{response.status_code} {response.reason_phrase}')

        return response.text
