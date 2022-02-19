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
        verbose_name='Регион',
        to='common.Region',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    class Meta:
        managed = False
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
    free_capacity = models.FloatField(
        verbose_name='Свободный объем',
        blank=True,
        null=True,
    )
    inflow = models.FloatField(
        verbose_name='Приток',
        blank=True,
        null=True,
    )
    outflow = models.FloatField(
        verbose_name='Средний сброс',
        blank=True,
        null=True,
        )
    spillway = models.FloatField(
        verbose_name='Холостой сброс',
        blank=True,
        null=True,
    )
    reservoir = models.ForeignKey(
        to=Reservoir,
        verbose_name='Водохранилище',
        on_delete=models.CASCADE,
    )

    class Meta:
        managed = False
        db_table = 'water_situation'
        verbose_name = 'Гидрологическая обстановка'
        verbose_name_plural = 'Гидрологическая обстановка'
        unique_together = (
            ('date', 'reservoir'),
        )

    def __str__(self):
        return self.name
