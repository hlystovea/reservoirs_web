from email.policy import default
from rest_framework.serializers import (FloatField, IntegerField,
                                        ModelSerializer, SerializerMethodField)

from reservoirs.models import Reservoir, WaterSituation


class ReservoirSerializer(ModelSerializer):
    class Meta:
        model = Reservoir
        fields = '__all__'


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
