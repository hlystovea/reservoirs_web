from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ReadOnlyModelViewSet

from reservoirs.filters import SituationFilter
from reservoirs.models import Reservoir, WaterSituation
from reservoirs.serializers import (ReservoirSerializer,
                                    WaterSituationSerializer)


class ReservoirsViewSet(ReadOnlyModelViewSet):
    queryset = Reservoir.objects.order_by('id')
    serializer_class = ReservoirSerializer


class WaterSituationsViewSet(ReadOnlyModelViewSet):
    queryset = WaterSituation.objects.order_by('date')
    serializer_class = WaterSituationSerializer
    filter_backends = (DjangoFilterBackend, )
    filter_class = SituationFilter
