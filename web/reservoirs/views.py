from django.db.models import Avg, F, Max, Sum, Window
from django.db.models.functions import Extract, ExtractYear, Lag, Round
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet

from reservoirs.filters import ReservoirFilter
from reservoirs.models import Reservoir, WaterSituation
from reservoirs.serializers import (ActualSituationSerializer,
                                    ReservoirSerializer,
                                    SituationSerializer,
                                    StatisticsByDaySerializer,
                                    YearSummarySerializer)


class ReservoirViewSet(ReadOnlyModelViewSet):
    serializer_class = ReservoirSerializer
    filterset_class = ReservoirFilter
    queryset = Reservoir.objects.select_related(
        'region'
    ).order_by(
        'region',
        'id'
    )


class SituationViewSet(GenericViewSet):
    queryset = WaterSituation.objects.order_by('date')
    serializer_class = SituationSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(reservoir=self.kwargs['reservoir_pk'])

    def create(self, request, *args, **kwargs):
        reservoir = get_object_or_404(Reservoir, pk=kwargs['reservoir_pk'])

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        queryset = WaterSituation.objects.filter(
            reservoir=reservoir, date=serializer.validated_data['date'])

        if queryset.exists():
            raise ValidationError({'detail': 'The situation already exists'})

        serializer.save(reservoir=reservoir)
        return Response(serializer.data, status=HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        reservoir = get_object_or_404(Reservoir, pk=kwargs['reservoir_pk'])
        params = [reservoir.pk]

        start = request.query_params.get('start')
        end = request.query_params.get('end')

        placeholders = []
        if start:
            placeholders.append('date >= %s')
            params.append(start)
        if end:
            placeholders.append('date <= %s')
            params.append(end)

        query = '''
            SELECT *
            FROM (
            SELECT *, ROUND(AVG(inflow) OVER w) AS avg_inflow
            FROM water_situation
            WHERE reservoir_id = %s
            WINDOW w AS (PARTITION BY DATE_PART('doy', date))
            ) as ws
        '''

        if start or end:
            select_criteria = ' AND '.join(placeholders)
            query += f' WHERE {select_criteria}'

        query += ' ORDER BY date'

        objs = WaterSituation.objects.raw(raw_query=query, params=params)

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

    def get_serializer_class(self):
        if self.get_view_name() == 'Year summary':
            return YearSummarySerializer
        return StatisticsByDaySerializer

    @action(methods=['get'], url_name='year-summary', detail=False)
    def year_summary(self, request, *args, **kwargs):
        queryset = self.get_queryset().annotate(
            year=ExtractYear('date')
        ).values(
            'year'
        ).annotate(
            max_inflow=Max('inflow'),
            inflow_volume=Sum('inflow')*8.64e-5,
            outflow_volume=Sum('outflow')*8.64e-5,
            spillway_volume=Sum('spillway')*8.64e-5
        ).order_by(
            'year'
        )

        serializer = self.get_serializer(queryset, many=True)
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

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
