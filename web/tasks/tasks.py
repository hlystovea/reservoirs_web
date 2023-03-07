from celery.utils.log import get_task_logger
from httpx import HTTPError

from web.celery import app
from services.scrapers import KrasScraper, RushydroScraper

logger = get_task_logger(__name__)


@app.task(autoretry_for=(HTTPError, ), retry_backoff=20)
def run_rushydro_parsing():
    RushydroScraper.scrape()
    return True


@app.task(autoretry_for=(HTTPError, ), retry_backoff=20)
def run_kras_parsing():
    KrasScraper.scrape()
    return True
