from django.db.models import Avg, F, Max, Sum, Window
from django.db.models.functions import Extract, ExtractYear, Lag, Round
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet

from reservoirs.filters import ReservoirFilter, SituationFilter
from reservoirs.models import Reservoir, WaterSituation
from reservoirs.serializers import (ActualSituationSerializer,
                                    ReservoirSerializer, SituationSerializer,
                                    StatisticsByDaySerializer,
                                    YearSummarySerializer)
from reservoirs.utils import date_parse, get_earlist_date


class ReservoirViewSet(ReadOnlyModelViewSet):
    serializer_class = ReservoirSerializer
    filterset_class = ReservoirFilter
    queryset = Reservoir.objects.select_related(
        'region'
    ).order_by(
        'region',
        'id'
    )


class WaterSituationView(APIView):
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

        serializer = SituationSerializer(objs, many=True)
        return Response(serializer.data)


class SituationViewSet(GenericViewSet):
    queryset = WaterSituation.objects.order_by('date')
    serializer_class = SituationSerializer
    filterset_class = SituationFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(reservoir=self.kwargs['reservoir_pk'])

    def list(self, request, *args, **kwargs):
        start = request.query_params.get('start', get_earlist_date())
        end = request.query_params.get('end', now().date().isoformat())

        reservoir = get_object_or_404(Reservoir, pk=kwargs['reservoir_pk'])

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

        serializer = SituationSerializer(objs, many=True)
        return Response(serializer.data)

    @action(methods=['get'], url_name='actual', detail=False)
    def actual(self, request, *args, **kwargs):
        queryset = self.get_queryset().annotate(
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
        ).latest('date')

        serializer = ActualSituationSerializer(queryset)
        return Response(serializer.data)


class StatisticsViewSet(GenericViewSet):
    queryset = WaterSituation.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(reservoir=self.kwargs['reservoir_pk'])

    @action(methods=['get'], url_name='year-summary', detail=False)
    def year_summary(self, request, *args, **kwargs):
        queryset = self.get_queryset().annotate(
            year=ExtractYear('date')
        ).values(
            'year'
        ).annotate(
            max_level=Max('level'),
            inflow_volume=Sum('inflow')*8.64e-5,
            outflow_volume=Sum('outflow')*8.64e-5,
            spillway_volume=Sum('spillway')*8.64e-5
        ).order_by(
            'year'
        )

        serializer = YearSummarySerializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['get'], url_name='day-of-year', detail=False)
    def day_of_year(self, request, *args, **kwargs):
        queryset = self.get_queryset().annotate(
            day_of_year=Extract('date', 'doy')
        ).values(
            'day_of_year'
        ).annotate(
            max_inflow=Max('inflow'),
            avg_inflow=Round(Avg('inflow')),
            avg_outflow=Round(Avg('outflow')),
            avg_spillway=Round(Avg('spillway'))
        ).order_by(
            'day_of_year'
        )

        serializer = StatisticsByDaySerializer(queryset, many=True)
        return Response(serializer.data)
