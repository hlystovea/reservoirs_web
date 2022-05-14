import datetime as dt
import logging
from os import environ
from typing import List, Optional

import asyncpg
from pydantic import parse_obj_as

from db.schemas import GeoObject, Region, Reservoir, WaterSituation, Weather


class PostgresDB:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.pool: Optional[asyncpg.Pool] = None

    async def setup(self):
        self.pool = await asyncpg.create_pool(self.dsn, min_size=1, max_size=5)
        logging.info('Start DB')

    async def stop(self):
        if self.pool:
            await self.pool.close()
            logging.info('Stop DB')

    async def insert_one(self, obj: WaterSituation) -> asyncpg.Record:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                '''
                INSERT INTO water_situation (date, level, free_capacity,
                inflow, outflow, spillway, reservoir_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7);
                ''',
                obj.date,
                obj.level,
                obj.free_capacity,
                obj.inflow,
                obj.outflow,
                obj.spillway,
                obj.reservoir_id,
            )

    async def insert_one_geo(self, obj: Weather) -> asyncpg.Record:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                '''
                INSERT INTO weather_weather (date, temp, pressure,
                humidity, cloudiness, wind_speed, wind_direction,
                precipitation, is_observable, geo_object_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10);
                ''',
                obj.date,
                obj.temp,
                obj.pressure,
                obj.humidity,
                obj.cloudiness,
                obj.wind_speed,
                obj.wind_direction,
                obj.precipitation,
                obj.is_observable,
                obj.geo_object_id,
            )

    async def check_existence(self, obj) -> bool:
        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                '''
                SELECT EXISTS (
                    SELECT *
                    FROM water_situation
                    WHERE date=$1 AND reservoir_id=$2
                    LIMIT 1
                );
                ''',
                obj.date,
                obj.reservoir_id,
            )

    async def check_existence_weather(self, obj) -> bool:
        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                '''
                SELECT EXISTS (
                    SELECT *
                    FROM weather_weather
                    WHERE date=$1 AND geo_object_id=$2
                    LIMIT 1
                );
                ''',
                obj.date,
                obj.geo_object_id,
            )

    async def get_last_date(self) -> Optional[dt.date]:
        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                '''
                SELECT MAX(date) AS last_date
                FROM water_situation
                GROUP BY reservoir_id
                ORDER BY last_date
                LIMIT 1
                '''
            )

    async def get_reservoir_by_slug(self, slug: str) -> Optional[Reservoir]:
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(
                '''
                SELECT *
                FROM reservoirs
                WHERE slug=$1
                LIMIT 1;
                ''',
                slug,
            )
            return Reservoir(**result)

    async def get_all_reservoirs(self) -> List[Reservoir]:
        async with self.pool.acquire() as conn:
            result = await conn.fetch('SELECT * FROM reservoirs;')
            return parse_obj_as(List[Reservoir], result)

    async def get_all_regions(self) -> List[Region]:
        async with self.pool.acquire() as conn:
            result = await conn.fetch('SELECT * FROM regions;')
            return parse_obj_as(List[Region], result)

    async def get_all_geo_objects(self) -> List[GeoObject]:
        async with self.pool.acquire() as conn:
            result = await conn.fetch('SELECT * FROM weather_geoobject;')
            return parse_obj_as(List[GeoObject], result)

    async def get_reservoirs_by_region(
        self, region_slug: str
    ) -> List[Reservoir]:
        async with self.pool.acquire() as conn:
            result = await conn.fetch(
                '''
                SELECT *
                FROM reservoirs
                WHERE region_id=(
                    SELECT id
                    FROM regions
                    WHERE slug=$1
                );
                ''',
                region_slug,
            )
            return parse_obj_as(List[Reservoir], result)

    async def get_water_situations_by_date(
        self, reservoir: Reservoir, date1: dt.date, date2: dt.date
    ) -> List[WaterSituation]:
        async with self.pool.acquire() as conn:
            result = await conn.fetch(
                '''
                SELECT *
                FROM water_situation
                WHERE reservoir_id=$1 AND date BETWEEN $2 AND $3
                ORDER BY date ASC;
                ''',
                reservoir.id,
                date1,
                date2,
            )
            return parse_obj_as(List[WaterSituation], result)


db = PostgresDB(environ['DATABASE_URL'])
