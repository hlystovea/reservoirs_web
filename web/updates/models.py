from django.db import models


class Update(models.Model):
    text = models.TextField(
        verbose_name='Текст записи',
        help_text='Обязательное поле',
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
    )
    image = models.ImageField(
        upload_to='updates/',
        verbose_name='Изображение',
        blank=True,
        null=True,
        help_text='Необязательное поле'
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Обновление'
        verbose_name_plural = 'Обновления'

    def __str__(self):
        return self.text[:15]
