from rest_framework.serializers import FloatField, ModelSerializer

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
