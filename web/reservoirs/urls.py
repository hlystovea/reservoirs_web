from django.urls import include, path
from rest_framework.routers import DefaultRouter

from reservoirs.views import ReservoirsViewSet, WaterSituationsViewSet

v1_router = DefaultRouter()

v1_router.register(r'situations', WaterSituationsViewSet, basename='situation')
v1_router.register(r'reservoirs', ReservoirsViewSet, basename='reservoir')


app_name = 'reservoirs'

urlpatterns = [
    path('v1/', include((v1_router.urls, 'v1'))),
]
