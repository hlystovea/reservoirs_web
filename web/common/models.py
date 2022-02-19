from django.db import models


class Region(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=64,
    )
    slug = models.CharField(
        verbose_name='Слаг',
        unique=True,
        max_length=64,
    )

    class Meta:
        db_table = 'regions'
        verbose_name = 'Регион'
        verbose_name_plural = 'Регионы'

    def __str__(self):
        return self.name
