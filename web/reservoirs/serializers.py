from rest_framework.reverse import reverse
from rest_framework.serializers import (FloatField, HyperlinkedIdentityField,
                                        IntegerField, ModelSerializer,
                                        Serializer, SerializerMethodField)

from common.serializers import RegionNestedSerializer
from reservoirs.models import Reservoir, WaterSituation


class ReservoirSerializer(ModelSerializer):
    url = HyperlinkedIdentityField(view_name='reservoirs:reservoir-detail')
    region = RegionNestedSerializer()
    water_situations = SerializerMethodField()
    actual_situation = SerializerMethodField()
    year_summary = SerializerMethodField()
    statistics_by_doy = SerializerMethodField()

    class Meta:
        model = Reservoir
        fields = '__all__'

    def get_water_situations(self, obj):
        return reverse('reservoirs:situation-list', args=(obj.id, ))

    def get_actual_situation(self, obj):
        return reverse('reservoirs:situation-actual', args=(obj.id, ))

    def get_year_summary(self, obj):
        return reverse('reservoirs:statistics-year-summary', args=(obj.id, ))

    def get_statistics_by_doy(self, obj):
        return reverse('reservoirs:statistics-day-of-year', args=(obj.id, ))


class SituationSerializer(ModelSerializer):
    avg_inflow = IntegerField(read_only=True)

    class Meta:
        model = WaterSituation
        exclude = ['id', 'reservoir', 'free_capacity']


class ActualSituationSerializer(ModelSerializer):
    level_offset = SerializerMethodField(read_only=True)
    inflow_offset = SerializerMethodField(read_only=True)
    outflow_offset = SerializerMethodField(read_only=True)
    spillway_offset = SerializerMethodField(read_only=True)

    class Meta:
        model = WaterSituation
        exclude = ['id', 'reservoir']

    def get_level_offset(self, obj):
        return f'{obj.level_offset:+.2f}'

    def get_inflow_offset(self, obj):
        if obj.inflow_offset is None:
            return 'н/д'
        return f'{obj.inflow_offset:+d}'

    def get_outflow_offset(self, obj):
        if obj.outflow_offset is None:
            return 'н/д'
        return f'{obj.outflow_offset:+d}'

    def get_spillway_offset(self, obj):
        if obj.spillway_offset is None:
            return 'н/д'
        return f'{obj.spillway_offset:+d}'


class YearSummarySerializer(Serializer):
    year = IntegerField(read_only=True)
    max_inflow = IntegerField(read_only=True)
    inflow_volume = FloatField(read_only=True)
    outflow_volume = FloatField(read_only=True)
    spillway_volume = FloatField(read_only=True)


class StatisticsByDaySerializer(Serializer):
    day_of_year = IntegerField(read_only=True)
    max_inflow = IntegerField(read_only=True)
    avg_inflow = IntegerField(read_only=True)
    avg_outflow = IntegerField(read_only=True)
    avg_spillway = IntegerField(read_only=True)
