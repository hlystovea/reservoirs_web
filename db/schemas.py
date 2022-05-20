from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, root_validator


class Reservoir(BaseModel):
    id: Optional[int]
    name: str
    slug: str
    force_level: float
    normal_level: float
    dead_level: float
    region_id: int
    useful_volume: Optional[float]
    full_volume: Optional[float]
    area: Optional[float]
    max_depth: Optional[float]

    class Config:
        orm_mode = True


class Situation(BaseModel):
    date: date
    reservoir_id: int
    level: float
    free_capacity: Optional[float]
    inflow: Optional[float]
    outflow: Optional[float]
    spillway: Optional[float]

    class Config:
        orm_mode = True

    @root_validator(pre=True)
    def check_fields(cls, values):  # noqa (N805)
        for key, value in values.items():
            if isinstance(value, str) and 'нет' in value:
                values[key] = None
        return values


class Region(BaseModel):
    id: Optional[int]
    name: str
    slug: str

    class Config:
        orm_mode = True


class GeoObject(BaseModel):
    id: Optional[int]
    name: str
    slug: str
    station_id: Optional[int]
    gismeteo_id: Optional[int]
    latitude: Optional[float]
    longitude: Optional[float]

    class Config:
        orm_mode = True


class Weather(BaseModel):
    date: datetime
    geo_object_id: Optional[int]
    temp: float
    pressure: int
    humidity: int
    cloudiness: int
    wind_speed: float
    wind_direction: int
    precipitation: float
    is_observable: bool

    class Config:
        orm_mode = True


class Gismeteo(Weather):
    def __init__(self, **kwargs):
        kwargs['temp'] = kwargs['temperature']['air']['C']
        kwargs['pressure'] = kwargs['pressure']['mm_hg_atm']
        kwargs['humidity'] = kwargs['humidity']['percent']
        kwargs['cloudiness'] = kwargs['cloudiness']['percent']
        kwargs['wind_speed'] = kwargs['wind']['speed']['m_s']
        kwargs['wind_direction'] = kwargs['wind']['direction']['scale_8']
        kwargs['precipitation'] = kwargs['precipitation']['amount'] or 0
        kwargs['is_observable'] = True if kwargs['kind'] == 'Obs' else False
        kwargs['date'] = datetime.strptime(
            kwargs['date']['UTC'], '%Y-%m-%d %H:%M:%S'
        )
        super().__init__(**kwargs)
