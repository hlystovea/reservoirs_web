from celery.utils.log import get_task_logger
from httpx import HTTPError

from web.celery import app
from services.scrapers import (GismeteoScraper, KrasScraper,
                               RoshydrometScraper, RP5Scraper, RushydroScraper)

logger = get_task_logger(__name__)


@app.task(autoretry_for=(HTTPError, ), retry_backoff=20)
def run_rushydro_parsing():
    RushydroScraper.scrape()
    return True


@app.task(autoretry_for=(HTTPError, ), retry_backoff=20)
def run_kras_parsing():
    KrasScraper.scrape()
    return True


@app.task(time_limit=2*60*60)
def run_rp5_parsing():
    RP5Scraper.scrape()
    return True


@app.task
def run_gismeteo_parsing():
    GismeteoScraper.scrape()
    return True


@app.task(autoretry_for=(HTTPError, ), retry_backoff=20)
def run_roshydromet_parsing():
    RoshydrometScraper.scrape()
    return True
