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
