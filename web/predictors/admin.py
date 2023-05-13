from django.contrib import admin
from django.utils.html import format_html

from common.admin import ExportCsvMixin
from .models import WaterSituationForecast, WaterSituationPredictor


class MixinAdmin(admin.ModelAdmin):
    empty_value_display = '-пусто-'


@admin.register(WaterSituationPredictor)
class ReservoirAdmin(MixinAdmin):
    list_display = ('id', 'reservoir', 'geo_objects_count')
    list_filter = ('reservoir__name', )

    @admin.display(description='Кол-во объектов')
    def geo_objects_count(self, obj):
        objects_count = obj.geo_objects.count()
        return format_html(f'{objects_count} объектов')


@admin.register(WaterSituationForecast)
class WaterSituationForecastAdmin(MixinAdmin, ExportCsvMixin):
    list_display = ('id', 'reservoir_name', 'date',
                    'inflow', 'forecast_date', 'predictor')
    list_filter = ('predictor__reservoir', 'predictor')
    date_hierarchy = 'date'
    actions = ['export_as_csv']

    @admin.display(description='Наименование вдхр.')
    def reservoir_name(self, obj):
        return obj.predictor.reservoir.name

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'predictor'
        ).prefetch_related(
            'predictor__reservoir'
        )
