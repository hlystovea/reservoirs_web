from django.urls import include, path
from rest_framework.routers import DefaultRouter

from reservoirs.views import (ActualWaterSituationsView, ReservoirsViewSet,
                              WaterSituationsView)

v1_router = DefaultRouter()

v1_router.register(r'reservoirs', ReservoirsViewSet, basename='reservoir')


app_name = 'reservoirs'

urlpatterns = [
    path('v1/', include((v1_router.urls, 'v1'))),
    path('v1/situations/', WaterSituationsView.as_view(), name='situation-list'),  # noqa(E501)
    path('v1/situations/actual/', ActualWaterSituationsView.as_view(), name='situation-actual'),  # noqa(E501)
]
