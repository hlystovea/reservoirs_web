import datetime
import os
from typing import List, Optional

import asyncpg
from asyncpg import Record
from pydantic import parse_obj_as

from core.db.schemas import Reservoir, WaterSituation


async def get_connection():
    return await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB")
    )


async def get_connection_by_dsn():
    """
    POSTGRES_DSN = postgres://user:password@host:port/database
    """
    return await asyncpg.connect(os.getenv("POSTGRES_DSN"))


async def insert_one(conn, obj: WaterSituation) -> asyncpg.Record:
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


async def insert_many(conn, objs: List[WaterSituation]) -> List[Record]:
    return await conn.fetch(
        '''
        INSERT INTO water_situation (date, level, free_capacity,
        inflow, outflow, spillway, reservoir_id)
        VALUES ($1, $2, $3, $4, $5, $6, $7);
        ''',
        objs,
    )


async def check_existence(conn, obj) -> bool:
    row = await conn.fetchrow(
        '''
        SELECT EXISTS (
        SELECT * FROM water_situation WHERE date=$1 AND reservoir_id=$2 LIMIT 1
        );
        ''',
        obj.date,
        obj.reservoir_id,
    )
    return row['exists']


async def get_last_date(conn) -> Optional[datetime.date]:
    return await conn.fetchval(
        'SELECT date FROM water_situation ORDER BY date DESC;'
    )


async def get_all_reservoirs(conn) -> List[Reservoir]:
    result = await conn.fetch('SELECT * FROM reservoirs;')
    return parse_obj_as(List[Reservoir], result)
