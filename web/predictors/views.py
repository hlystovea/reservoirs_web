from django.db.models import OuterRef, Subquery
from rest_framework.viewsets import ReadOnlyModelViewSet

from predictors.models import WaterSituationForecast, WaterSituationPredictor
from predictors.serializers import PredictorSerializer, ForecastSerializer
from reservoirs.models import WaterSituation


class PredictorsViewSet(ReadOnlyModelViewSet):
    serializer_class = PredictorSerializer
    queryset = WaterSituationPredictor.objects.all()


class ForecastViewSet(ReadOnlyModelViewSet):
    serializer_class = ForecastSerializer
    queryset = WaterSituationForecast.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        fact_inflow = WaterSituation.objects.filter(
            reservoir=OuterRef('predictor__reservoir'),
            date=OuterRef('date')
        ).values('inflow')
        return queryset.annotate(fact=Subquery(fact_inflow)).order_by('date')
