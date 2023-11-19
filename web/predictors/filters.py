from django_filters import CharFilter, DateFilter, FilterSet

from predictors.models import WaterSituationForecast, WaterSituationPredictor


class PredictorFilter(FilterSet):
    reservoir = CharFilter(field_name='reservoir__slug')

    class Meta:
        model = WaterSituationPredictor
        fields = ['reservoir']


class ForecastFilter(FilterSet):
    start = DateFilter(field_name='date', lookup_expr='gte')
    end = DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model = WaterSituationForecast
        fields = ['start', 'end']
