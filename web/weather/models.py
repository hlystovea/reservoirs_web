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
