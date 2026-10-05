import datetime as dt
import re
import time
from abc import ABCMeta, abstractmethod
from os import environ as env
from typing import Optional
from urllib.parse import urljoin

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
from services.parsers import (AbstractParser, EbvuDocxParser, GismeteoParser,
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
    parser = EbvuDocxParser()
    base_url = env.get('EBVU_URL', 'https://en.favr.ru/node/1290')
    date_pattern = re.compile(r'(\d{2})\.(\d{2})\.(\d{4})')

    @classmethod
    def get_url(cls) -> str:
        return cls.base_url

    @classmethod
    def get_last_dates(cls) -> dict[str, Optional[dt.date]]:
        from django.db.models import Max

        rows = (
            WaterSituation.objects
            .filter(reservoir__slug__in=cls.parser.reservoir_names.values())
            .values('reservoir__slug')
            .annotate(last=Max('date'))
        )
        return {row['reservoir__slug']: row['last'] for row in rows}

    @classmethod
    def parse_date(cls, text: str) -> Optional[dt.date]:
        match = cls.date_pattern.search(text or '')

        if not match:
            return None

        day, month, year = map(int, match.groups())

        try:
            return dt.date(year, month, day)

        except ValueError:
            return None

    @classmethod
    def list_docx(cls, page: str) -> list[tuple[dt.date, str]]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(page, 'html.parser')
        found = []

        for link in soup.find_all('a', href=True):
            href = link['href']

            if not href.lower().endswith('.docx'):
                continue

            date = cls.parse_date(href) or cls.parse_date(
                link.get_text(separator=' ', strip=True))

            if date is None:
                logger.warning(f'{cls.__name__} no date in {href}')
                continue

            found.append((date, urljoin(cls.base_url, href)))

        return sorted(set(found))

    @classmethod
    def get_page(cls) -> str:
        with httpx.Client(verify=False) as client:
            response = client.get(cls.get_url(), follow_redirects=True)

        if response.is_error:
            raise httpx.HTTPError(
                f'{response.status_code} {response.reason_phrase}')

        return response.text

    @classmethod
    def get_file(cls, url: str) -> bytes:
        with httpx.Client(verify=False) as client:
            response = client.get(url, follow_redirects=True)

        if response.is_error:
            raise httpx.HTTPError(
                f'{response.status_code} {response.reason_phrase}')

        return response.content

    @classmethod
    def save(
        cls, date: dt.date, situation: Situation, reservoir: Reservoir
    ) -> tuple[Optional[WaterSituation], bool]:
        data = situation.dict(exclude_none=True)
        data.pop('date', None)

        try:
            return WaterSituation.objects.update_or_create(
                date=date,
                reservoir=reservoir,
                defaults=data
            )

        except DatabaseError as error:
            logger.error(f'{cls.__name__} {repr(error)}')
            return None, False

    @classmethod
    def scrape_file(cls, date, url, slugs, reservoirs, last_dates) -> int:
        needed = [
            slug for slug in slugs
            if date > last_dates.get(slug, dt.date.min)
        ]

        if not needed:
            return 0

        saved_count = 0

        try:
            content = cls.get_file(url)
            situations = cls.parser.parse(content, date)

            for slug, situation in situations.items():
                if slug not in needed:
                    continue

                reservoir = reservoirs.get(slug)

                if reservoir is None:
                    continue

                obj, created = cls.save(date, situation, reservoir)

                if obj is not None:
                    last_dates[slug] = date
                    saved_count += 1
                    action = 'created' if created else 'updated'
                    logger.info(
                        f'{cls.__name__} {action}: {reservoir} {date}'
                    )

        except httpx.HTTPError as error:
            logger.error(f'{cls.__name__} {error!r}')

        return saved_count

    @classmethod
    def scrape(cls):
        logger.info(f'{cls.__name__} start scraping')

        slugs = list(cls.parser.reservoir_names.values())
        last_dates = cls.get_last_dates()
        page = cls.get_page()
        docx_list = cls.list_docx(page)

        logger.info(f'{cls.__name__} found {len(docx_list)} docx')

        reservoirs = {
            r.slug: r for r in Reservoir.objects.filter(slug__in=slugs)
        }

        for slug in slugs:
            if slug not in reservoirs:
                logger.warning(f'{cls.__name__} no reservoir for slug {slug}')

        saved_count = sum(
            cls.scrape_file(date, url, slugs, reservoirs, last_dates)
            for date, url in docx_list
        )

        logger.info(f'{cls.__name__} saved {saved_count} new objs')
        logger.info(f'{cls.__name__} stop scraping')


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
