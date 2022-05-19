from os import environ

import peewee
from peewee_async import PooledPostgresqlDatabase


POSTGRES_HOST = environ.get('POSTGRES_HOST')
POSTGRES_DB = environ.get('POSTGRES_DB')
POSTGRES_USER = environ.get('POSTGRES_USER')
POSTGRES_PASSWORD = environ.get('POSTGRES_PASSWORD')

database = PooledPostgresqlDatabase(
    POSTGRES_DB,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
    host=POSTGRES_HOST,
    max_connections=20
)


class BaseModel(peewee.Model):
    class Meta:
        database = database


class RegionModel(BaseModel):
    id = peewee.BigAutoField()
    name = peewee.CharField(max_length=64)
    slug = peewee.CharField(max_length=64, unique=True, index=True)

    class Meta:
        table_name = 'regions'


class ReservoirModel(BaseModel):
    id = peewee.BigAutoField()
    name = peewee.CharField(max_length=64)
    slug = peewee.CharField(max_length=64, unique=True, index=True)
    area = peewee.DoubleField(null=True)
    max_depth = peewee.DoubleField(null=True)
    dead_level = peewee.DoubleField(null=True)
    force_level = peewee.DoubleField(null=True)
    full_volume = peewee.DoubleField(null=True)
    normal_level = peewee.DoubleField(null=True)
    useful_volume = peewee.DoubleField(null=True)
    region = peewee.ForeignKeyField(
        column_name='region_id', field='id', model=RegionModel, null=True
    )

    class Meta:
        table_name = 'reservoirs'


class SituationModel(BaseModel):
    id = peewee.BigAutoField()
    date = peewee.DateField()
    level = peewee.DoubleField()
    inflow = peewee.DoubleField(null=True)
    outflow = peewee.DoubleField(null=True)
    spillway = peewee.DoubleField(null=True)
    free_capacity = peewee.DoubleField(null=True)
    reservoir = peewee.ForeignKeyField(
        column_name='reservoir_id', field='id', model=ReservoirModel
    )

    class Meta:
        table_name = 'water_situation'
        indexes = (
            (('date', 'reservoir'), True),
        )


class GeoObjectModel(BaseModel):
    id = peewee.BigAutoField()
    name = peewee.CharField(max_length=64)
    slug = peewee.CharField(max_length=64, unique=True, index=True)
    station_id = peewee.IntegerField(null=True, unique=True)
    gismeteo_id = peewee.IntegerField(null=True, unique=True)
    latitude = peewee.DoubleField(null=True)
    longitude = peewee.DoubleField(null=True)

    class Meta:
        table_name = 'weather_geoobject'


class WeatherModel(BaseModel):
    id = peewee.BigAutoField()
    date = peewee.DateTimeField()
    temp = peewee.DoubleField()
    pressure = peewee.SmallIntegerField()
    cloudiness = peewee.SmallIntegerField()
    humidity = peewee.SmallIntegerField()
    precipitation = peewee.DoubleField()
    wind_speed = peewee.DoubleField()
    wind_direction = peewee.SmallIntegerField()
    is_observable = peewee.BooleanField(default=False)
    geo_object = peewee.ForeignKeyField(
        column_name='geo_object_id', field='id', model=GeoObjectModel
    )

    class Meta:
        table_name = 'weather_weather'
        indexes = (
            (('date', 'geo_object'), True),
        )
