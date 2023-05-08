from django.db import models


class WaterSituationPredictor(models.Model):
    reservoir = models.OneToOneField(
        to='reservoirs.Reservoir',
        to_field='id',
        verbose_name='Водохранилище',
        on_delete=models.CASCADE,
    )
    checkpoint = models.FileField(
        verbose_name='Модель',
        help_text='Файл состояния модели в формате ckpt',
        upload_to='predictors/checkpoints/',
    )
    geo_objects = models.ManyToManyField(
        to='weather.GeoObject',
        verbose_name='Географические объекты',
        related_name='predictors',
    )

    class Meta:
        verbose_name = 'Модель гидрологической обстановки'
        verbose_name_plural = 'Модели гидрологической обстановки'


class WaterSituationForecast(models.Model):
    date = models.DateField(
        verbose_name='Дата',
    )
    inflow = models.IntegerField(
        verbose_name='Приток',
    )
    reservoir = models.ForeignKey(
        to='reservoirs.Reservoir',
        to_field='id',
        verbose_name='Водохранилище',
        on_delete=models.CASCADE,
        related_name='forecasts',
    )
    forecast_date = models.DateTimeField(
        verbose_name='Время составления прогноза',
        auto_now=True,
    )

    class Meta:
        verbose_name = 'Прогноз гидрологической обстановки'
        verbose_name_plural = 'Прогнозы гидрологической обстановки'
        constraints = [
            models.UniqueConstraint(
                fields=['date', 'reservoir_id'],
                name='date_reservoir_id_unique_together',
            )
        ]