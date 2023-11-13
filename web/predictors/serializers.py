from rest_framework.reverse import reverse
from rest_framework.serializers import (IntegerField, ModelSerializer,
                                        SerializerMethodField)

from predictors.models import WaterSituationForecast, WaterSituationPredictor


class PredictorSerializer(ModelSerializer):
    forecast = SerializerMethodField()

    class Meta:
        model = WaterSituationPredictor
        fields = '__all__'

    def get_forecast(self, obj):
        request = self.context['request']
        viewname = 'predictors:forecast-list'
        return reverse(viewname, args=(obj.id, ), request=request)


class ForecastSerializer(ModelSerializer):
    fact = IntegerField()

    class Meta:
        model = WaterSituationForecast
        fields = '__all__'
