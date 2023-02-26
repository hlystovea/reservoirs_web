from celery.utils.log import get_task_logger
from httpx import HTTPError

from web.celery import app
from services.parsers import KrasParser, RushydroParser

logger = get_task_logger(__name__)


@app.task(autoretry_for=(HTTPError, ), retry_backoff=20)
def run_rushydro_parsing():
    RushydroParser().worker()
    return True


@app.task(autoretry_for=(HTTPError, ), retry_backoff=20)
def run_kras_parsing():
    KrasParser().worker()
    return True
