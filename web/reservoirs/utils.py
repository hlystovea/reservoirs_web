from datetime import timedelta

from dateutil.parser import parse, ParserError
from django.utils.timezone import now
from rest_framework.exceptions import ParseError

from reservoirs.models import WaterSituation


def get_earlist_date() -> str:
    try:
        return WaterSituation.objects.earliest('date').date.isoformat()
    except WaterSituation.DoesNotExist:
        return '1970-01-01'


def get_date_before(days_before: int = 90) -> str:
    return (now().date() - timedelta(days=days_before)).isoformat()


def date_parse(date: str):
    try:
        return parse(date).date().isoformat()
    except ParserError:
        raise ParseError(f'Неверный формат даты: {date}')
