from rest_framework.serializers import ModelSerializer

from reservoirs.models import Reservoir, WaterSituation


class ReservoirSerializer(ModelSerializer):
    class Meta:
        model = Reservoir
        fields = '__all__'


class WaterSituationSerializer(ModelSerializer):
    class Meta:
        model = WaterSituation
        fields = '__all__'
