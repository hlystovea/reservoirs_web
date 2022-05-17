from django.db.models import F, Window
from django.db.models.functions import Lag
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from reservoirs.models import Reservoir, WaterSituation
from reservoirs.serializers import (ActualWaterSituationSerializer,
                                    ReservoirSerializer,
                                    WaterSituationSerializer)
from reservoirs.utils import get_earlist_date, date_parse


class ReservoirsViewSet(ReadOnlyModelViewSet):
    queryset = Reservoir.objects.order_by('id')
    serializer_class = ReservoirSerializer


class WaterSituationsView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        slug = request.query_params.get('reservoir', 'sayano')
        start = date_parse(request.query_params.get('start', get_earlist_date()))  # noqa(E501)
        end = date_parse(request.query_params.get('end', now().date().isoformat()))  # noqa(E501)

        reservoir = get_object_or_404(Reservoir, slug=slug)

        raw_query = '''
            WITH ws AS (
            SELECT *, avg(inflow) OVER w AS avg_inflow
            FROM water_situation
            WHERE reservoir_id = %s
            WINDOW w AS (PARTITION BY DATE_PART('doy', date))
            )
            SELECT *
            FROM ws
            WHERE date BETWEEN %s AND %s
            ORDER BY date
        '''
        params = [reservoir.id, start, end]

        objs = WaterSituation.objects.raw(raw_query=raw_query, params=params)

        serializer = WaterSituationSerializer(objs, many=True)
        return Response(serializer.data)


class ActualWaterSituationsView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        reservoir_slug = request.query_params.get('reservoir', 'sayano')
        reservoir = get_object_or_404(Reservoir, slug=reservoir_slug)

        situation = reservoir.situations.annotate(
            level_offset=F('level') - Window(
                expression=Lag('level'),
                order_by=F('date').asc(),
            ),
            inflow_offset=F('inflow') - Window(
                expression=Lag('inflow'),
                order_by=F('date').asc(),
            ),
            outflow_offset=F('outflow') - Window(
                expression=Lag('outflow'),
                order_by=F('date').asc(),
            ),
            spillway_offset=F('spillway') - Window(
                expression=Lag('spillway'),
                order_by=F('date').asc(),
            )
        ).last()
        serializer = ActualWaterSituationSerializer(situation)
        return Response(serializer.data)
