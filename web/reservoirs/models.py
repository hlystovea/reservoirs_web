from django.db import models


class Reservoir(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=64,
    )
    slug = models.CharField(
        verbose_name='Слаг',
        unique=True,
        max_length=64,
    )
    station_name = models.CharField(
        verbose_name='Название ГЭС',
        unique=True,
        max_length=64,
        blank=True,
        null=True,
    )
    force_level = models.FloatField(
        verbose_name='ФПУ',
        max_length=64,
        blank=True,
        null=True,
    )
    normal_level = models.FloatField(
        verbose_name='НПУ',
        max_length=64,
        blank=True,
        null=True,
    )
    dead_level = models.FloatField(
        verbose_name='УМО',
        max_length=64,
        blank=True,
        null=True,
    )
    region = models.ForeignKey(
        to='common.Region',
        to_field='id',
        verbose_name='Регион',
        on_delete=models.SET_NULL,
        related_name='reservoirs',
        blank=True,
        null=True,
    )
    useful_volume = models.FloatField(
        verbose_name='Полезный объем',
        help_text='Полезный объем водохранилища в км\u00b3',
        max_length=64,
        blank=True,
        null=True,
    )
    full_volume = models.FloatField(
        verbose_name='Полный объем',
        help_text='Полный объем водохранилища в км\u00b3',
        max_length=64,
        blank=True,
        null=True,
    )
    area = models.FloatField(
        verbose_name='Площадь',
        help_text='Площадь водохранилища в км\u00b2',
        max_length=64,
        blank=True,
        null=True,
    )
    max_depth = models.FloatField(
        verbose_name='Максимальная глубина',
        max_length=64,
        blank=True,
        null=True,
    )

    class Meta:
        db_table = 'reservoirs'
        verbose_name = 'Водохранилище'
        verbose_name_plural = 'Водохранилища'

    def __str__(self):
        return self.name


class WaterSituation(models.Model):
    date = models.DateField(
        verbose_name='Дата',
    )
    level = models.FloatField(
        verbose_name='УВБ',
    )
    free_capacity = models.IntegerField(
        verbose_name='Свободный объем',
        blank=True,
        null=True,
    )
    inflow = models.IntegerField(
        verbose_name='Приток',
        blank=True,
        null=True,
    )
    outflow = models.IntegerField(
        verbose_name='Средний сброс',
        blank=True,
        null=True,
        )
    spillway = models.IntegerField(
        verbose_name='Холостой сброс',
        blank=True,
        null=True,
    )
    reservoir = models.ForeignKey(
        to='reservoirs.Reservoir',
        to_field='id',
        verbose_name='Водохранилище',
        on_delete=models.CASCADE,
        related_name='situations',
    )

    class Meta:
        db_table = 'water_situation'
        verbose_name = 'Гидрологическая обстановка'
        verbose_name_plural = 'Гидрологическая обстановка'
        constraints = [
            models.UniqueConstraint(
                fields=['date', 'reservoir_id'],
                name='water_situation_date_reservoir_id_key',
            )
        ]

    def __str__(self):
        return f'{self.reservoir.name}: {self.date}'
