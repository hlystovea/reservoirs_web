from rest_framework.reverse import reverse
from rest_framework.serializers import (IntegerField, ModelSerializer,
                                        SerializerMethodField,
                                        SlugRelatedField)

from predictors.models import WaterSituationForecast, WaterSituationPredictor
from reservoirs.models import Reservoir


class PredictorSerializer(ModelSerializer):
    forecast = SerializerMethodField()
    reservoir = SlugRelatedField(
        slug_field='name',
        queryset=Reservoir.objects.all(),
    )

    class Meta:
        model = WaterSituationPredictor
        fields = ('id', 'name', 'reservoir', 'forecast')

    def get_forecast(self, obj):
        request = self.context['request']
        viewname = 'predictors:forecast-list'
        return reverse(viewname, args=(obj.id, ), request=request)


class ForecastSerializer(ModelSerializer):
    fact = IntegerField()

    class Meta:
        model = WaterSituationForecast
        exclude = ('predictor', )
