# Generated by Django 4.0.6 on 2022-07-24 07:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_initial'),
        ('reservoirs', '0005_alter_watersituation_free_capacity_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reservoir',
            name='region',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reservoirs', to='common.region', verbose_name='Регион'),
        ),
    ]