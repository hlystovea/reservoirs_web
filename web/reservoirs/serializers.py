from rest_framework.serializers import IntegerField, FloatField, ModelSerializer

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
    level_offset = FloatField(read_only=True)
    inflow_offset = IntegerField(read_only=True)
    outflow_offset = IntegerField(read_only=True)
    spillway_offset = IntegerField(read_only=True)

    class Meta:
        model = WaterSituation
        fields = '__all__'
