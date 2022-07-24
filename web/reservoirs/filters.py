from django_filters import CharFilter, DateFilter, FilterSet

from reservoirs.models import Reservoir, WaterSituation


class SituationFilter(FilterSet):
    reservoir = CharFilter(field_name='reservoir__slug')

    start = DateFilter(field_name='date', lookup_expr='gte')
    end = DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model = WaterSituation
        fields = ['reservoir', 'start', 'end']


class ReservoirFilter(FilterSet):
    region = CharFilter(field_name='region__slug')

    class Meta:
        model = Reservoir
        fields = ['region']
