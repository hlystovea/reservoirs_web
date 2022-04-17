from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from reservoirs.models import Reservoir, WaterSituation
from reservoirs.serializers import (ReservoirSerializer,
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
        end = date_parse(request.query_params.get('end', now().date()))

        reservoir = get_object_or_404(Reservoir, slug=slug)

        objs = WaterSituation.objects.raw(
            raw_query='''
            SELECT ws1.*, ws2.day_of_year, ws2.avg_inflow
            FROM water_situation AS ws1
            LEFT JOIN (
                SELECT
                    DATE_PART('doy', date) AS  day_of_year,
                    AVG(inflow) AS avg_inflow,
                    reservoir_id
                FROM water_situation
                GROUP BY day_of_year, reservoir_id
            ) AS ws2
            ON DATE_PART('doy', ws1.date) = ws2.day_of_year
              AND ws1.reservoir_id = ws2.reservoir_id
            WHERE ws1.reservoir_id = %s AND ws1.date BETWEEN %s AND %s
            ORDER BY ws1.date ASC
            ''',
            params=[reservoir.id, start, end],
        )

        serializer = WaterSituationSerializer(objs, many=True)
        return Response(serializer.data)
