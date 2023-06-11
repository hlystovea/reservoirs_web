import re
import datetime as dt
from typing import Optional

from dateutil.parser import parse as parse_date
from pydantic import BaseModel, root_validator, validator


class WeatherBase(BaseModel):
    date: dt.datetime
    temp: float
    pressure: int
    humidity: int
    cloudiness: int
    wind_speed: float
    precipitation: float
    is_observable: bool = False


class RP5(WeatherBase):
    is_observable: bool = True

    def __init__(self, **kwargs):
        kwargs['temp'] = kwargs['T']
        kwargs['pressure'] = kwargs['Po']
        kwargs['humidity'] = kwargs['U']
        kwargs['cloudiness'] = kwargs['N']
        kwargs['wind_speed'] = kwargs['Ff']
        kwargs['precipitation'] = kwargs['RRR']
        super().__init__(**kwargs)

    @validator('pressure', 'precipitation', pre=True)
    def field_must_be_float(cls, value):
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0

    @validator('cloudiness', 'wind_speed', pre=True)
    def field_must_be_integer(cls, value):
        try:
            return int(re.search(r'\d+', value).group())
        except (ValueError, TypeError, AttributeError):
            return 0


class Gismeteo(WeatherBase):
    def __init__(self, **kwargs):
        kwargs['temp'] = kwargs['temperature']['air']['C']
        kwargs['pressure'] = kwargs['pressure']['mm_hg_atm']
        kwargs['humidity'] = kwargs['humidity']['percent']
        kwargs['cloudiness'] = kwargs['cloudiness']['percent']
        kwargs['wind_speed'] = kwargs['wind']['speed']['m_s']
        kwargs['precipitation'] = kwargs['precipitation']['amount'] or 0
        kwargs['date'] = dt.datetime.strptime(
            kwargs['date']['local'], '%Y-%m-%d %H:%M:%S'
        )
        super().__init__(**kwargs)


class Roshydromet(WeatherBase):
    humidity: int = 50

    @validator('wind_speed', pre=True)
    def field_must_be_integer(cls, value):
        try:
            return int(re.search(r'\d+', value).group())
        except (ValueError, TypeError, AttributeError):
            return 0


class Situation(BaseModel):
    date: Optional[dt.date]
    level: float
    free_capacity: Optional[int]
    inflow: Optional[int]
    outflow: Optional[int]
    spillway: Optional[int]

    class Config:
        orm_mode = True

    @root_validator(pre=True)
    def check_fields(cls, values):
        for key, value in values.items():
            if isinstance(value, str) and 'нет' in value:
                values[key] = None
        return values


class RushydroSituation(Situation):
    @validator('date', pre=True)
    def parsedate(cls, value):
        today = dt.date.today()
        year = today.year - (today.month < int(value.split('.')[-1]))
        return parse_date(f'{value}.{year}', dayfirst=True)
