from django.db import models
from django.core import validators


class GeoObject(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=64,
    )
    slug = models.CharField(
        verbose_name='Слаг',
        unique=True,
        max_length=64,
    )
    station_id = models.IntegerField(
        verbose_name='Номер метеостанции',
        unique=True,
        blank=True,
        null=True,
    )
    gismeteo_id = models.IntegerField(
        verbose_name='ID географического объекта (Gismeteo)',
        unique=True,
        blank=True,
        null=True,
    )
    latitude = models.FloatField(
        verbose_name='Широта расположения географического объекта',
        blank=True,
        null=True,
        validators=[
            validators.MaxValueValidator(
                90,
                message='Широта не может быть больше 90',
            ),
            validators.MinValueValidator(
                -90,
                message='Широта не может быть меньше -90',
            )
        ]
    )
    longitude = models.FloatField(
        verbose_name='Долгота расположения географического объекта',
        blank=True,
        null=True,
        validators=[
            validators.MaxValueValidator(
                180,
                message='Долгота не может быть больше 180',
            ),
            validators.MinValueValidator(
                -180,
                message='Долгота не может быть меньше -180',
            )
        ]
    )

    class Meta:
        ordering = ('name', )
        verbose_name = 'Географический объект'
        verbose_name_plural = 'Географические объекты'

    def __str__(self):
        return self.name


class Weather(models.Model):
    date = models.DateTimeField(
        verbose_name='Дата/Время',
    )
    geo_object = models.ForeignKey(
        to=GeoObject,
        verbose_name='Географический объект',
        on_delete=models.CASCADE,
        related_name='weather',
    )
    temp = models.FloatField(
        verbose_name='Температура воздуха',
    )
    pressure = models.PositiveSmallIntegerField(
        verbose_name='Атмосферное давление',
    )
    humidity = models.PositiveSmallIntegerField(
        verbose_name='Влажность',
        validators=[
            validators.MaxValueValidator(
                100,
                message='Влажность не может быть больше 100 %',
            ),
        ],
    )
    cloudiness = models.PositiveSmallIntegerField(
        verbose_name='Облачность',
        validators=[
            validators.MaxValueValidator(
                100,
                message='Облачность не может быть больше 100 %',
            ),
        ],
    )
    wind_speed = models.FloatField(
        verbose_name='Скорость ветра',
    )
    precipitation = models.FloatField(
        verbose_name='Осадки',
    )
    is_observable = models.BooleanField(
        verbose_name='На основе наблюдений',
        default=False,
    )

    class Meta:
        verbose_name = 'Погода'
        verbose_name_plural = 'Погода'
        constraints = [
            models.UniqueConstraint(
                fields=['date', 'geo_object'],
                name='weather_weather_date_geo_object_id',
            )
        ]

    def __str__(self):
        return f'{self.geo_object.name}: {self.date}'
