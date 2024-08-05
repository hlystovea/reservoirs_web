from celery.utils.log import get_task_logger
from httpx import HTTPError

from web.celery import app
from services.forecasting import water_situation_forecasting
from services.parsers import (BoguchanParser, BratskParser, IrkutskParser,
                              KrasParser, MainskParser, SayanParser,
                              UstIlimParser)
from services.scrapers import (GismeteoScraper, EbvuScraper,
                               RoshydrometScraper, RP5Scraper)

logger = get_task_logger(__name__)


@app.task(autoretry_for=(HTTPError, ), retry_backoff=20)
def run_kras_parsing():
    parser = KrasParser()
    EbvuScraper(parser, 'kras').scrape()
    return True


@app.task(autoretry_for=(HTTPError, ), retry_backoff=20)
def run_sayan_parsing():
    parser = SayanParser()
    EbvuScraper(parser, 'sayano').scrape()
    return True


@app.task(autoretry_for=(HTTPError, ), retry_backoff=20)
def run_mainsk_parsing():
    parser = MainskParser()
    EbvuScraper(parser, 'mainsk').scrape()
    return True


@app.task(autoretry_for=(HTTPError, ), retry_backoff=20)
def run_irkutsk_parsing():
    parser = IrkutskParser()
    EbvuScraper(parser, 'irkutsk').scrape()
    return True


@app.task(autoretry_for=(HTTPError, ), retry_backoff=20)
def run_bratsk_parsing():
    parser = BratskParser()
    EbvuScraper(parser, 'bratsk').scrape()
    return True


@app.task(autoretry_for=(HTTPError, ), retry_backoff=20)
def run_ust_ilim_parsing():
    parser = UstIlimParser()
    EbvuScraper(parser, 'ust-ilim').scrape()
    return True


@app.task(autoretry_for=(HTTPError, ), retry_backoff=20)
def run_boguchan_parsing():
    parser = BoguchanParser()
    EbvuScraper(parser, 'boguch').scrape()
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


@app.task
def run_water_situation_forecasting():
    water_situation_forecasting()
    return True
