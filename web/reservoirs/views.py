from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ReadOnlyModelViewSet

from reservoirs.filters import SituationFilter
from reservoirs.models import Reservoir, WaterSituation
from reservoirs.serializers import (ReservoirSerializer,
                                    WaterSituationSerializer)


class ReservoirsViewSet(ReadOnlyModelViewSet):
    queryset = Reservoir.objects.all()
    serializer_class = ReservoirSerializer


class WaterSituationsViewSet(ReadOnlyModelViewSet):
    queryset = WaterSituation.objects.all()
    serializer_class = WaterSituationSerializer
    filter_backends = (DjangoFilterBackend, )
    filter_class = SituationFilter
