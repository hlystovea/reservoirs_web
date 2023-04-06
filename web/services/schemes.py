import re
import datetime as dt
from typing import Optional

from pydantic import BaseModel, root_validator, validator


class Forecast(BaseModel):
    date: dt.datetime
    temp: float
    pressure: int
    humidity: int
    cloudiness: int
    wind_speed: float
    precipitation: float
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
