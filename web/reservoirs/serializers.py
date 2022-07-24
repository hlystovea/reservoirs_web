from rest_framework.reverse import reverse
from rest_framework.serializers import (FloatField, HyperlinkedIdentityField,
                                        ModelSerializer, SerializerMethodField)

from reservoirs.models import Reservoir, WaterSituation
from common.serializers import RegionNestedSerializer


class ReservoirSerializer(ModelSerializer):
    url = HyperlinkedIdentityField(view_name='reservoirs:reservoir-detail')
    region = RegionNestedSerializer()
    water_situations = SerializerMethodField()
    actual_situation = SerializerMethodField()

    class Meta:
        model = Reservoir
        fields = '__all__'

    def get_water_situations(self, obj):
        view_name = 'reservoirs:situation-list'
        base_url = reverse(view_name, request=self.context['request'])
        return f'{base_url}?reservoirs={obj.slug}'

    def get_actual_situation(self, obj):
        view_name = 'reservoirs:situation-actual'
        base_url = reverse(view_name, request=self.context['request'])
        return f'{base_url}?reservoirs={obj.slug}'


class WaterSituationSerializer(ModelSerializer):
    avg_inflow = FloatField(read_only=True)

    class Meta:
        model = WaterSituation
        fields = '__all__'


class ActualWaterSituationSerializer(ModelSerializer):
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
