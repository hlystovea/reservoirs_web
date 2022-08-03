from django.urls import include, path
from rest_framework_nested import routers

from reservoirs.views import (ReservoirViewSet, SituationViewSet,
                              StatisticsViewSet)

app_name = 'reservoirs'

v1_reservoirs = routers.SimpleRouter()
v1_reservoirs.register(r'reservoirs', ReservoirViewSet)

v1_situations = routers.NestedSimpleRouter(v1_reservoirs, r'reservoirs', lookup='reservoir')  # noqa(E501)
v1_situations.register(r'situations', SituationViewSet, basename='situation')  # noqa(E501)

v1_statistics = routers.NestedSimpleRouter(v1_reservoirs, r'reservoirs', lookup='reservoir')  # noqa(E501)
v1_statistics.register(r'statistics', StatisticsViewSet, basename='statistics')  # noqa(E501)

urlpatterns = [
    path('v1/', include(v1_reservoirs.urls)),
    path('v1/', include(v1_situations.urls)),
    path('v1/', include(v1_statistics.urls)),
]
