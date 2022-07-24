from django.urls import include, path
from rest_framework.routers import DefaultRouter

from reservoirs.views import (ActualWaterSituationsView, ReservoirsViewSet,
                              WaterSituationsView)


app_name = 'reservoirs'

v1_reservoirs = DefaultRouter()
v1_reservoirs.register(r'reservoirs', ReservoirsViewSet)

urlpatterns = [
    path('v1/', include(v1_reservoirs.urls)),
    path('v1/situations/', WaterSituationsView.as_view(), name='situation-list'),  # noqa(E501)
    path('v1/situations/actual/', ActualWaterSituationsView.as_view(), name='situation-actual'),  # noqa(E501)
]
