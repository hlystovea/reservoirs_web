# Generated by Django 4.0.6 on 2023-05-01 08:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weather', '0006_remove_weather_weather_weather_date_geo_object_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='geoobject',
            name='roshydromet_id',
            field=models.IntegerField(blank=True, null=True, unique=True, verbose_name='ID географического объекта (Росгидромет)'),
        ),
    ]
