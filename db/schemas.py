from datetime import date
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


class WaterSituation(BaseModel):
    id: Optional[int]
    date: date
    reservoir_id: int
    level: float
    free_capacity: Optional[float]
    inflow: Optional[float]
    outflow: Optional[float]
    spillway: Optional[float]

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
