from django.urls import include, path
from rest_framework.routers import DefaultRouter

from common.views import RegionsViewSet


app_name = 'common'

regions_router = DefaultRouter()
regions_router.register(r'regions', RegionsViewSet)

urlpatterns = [
    path('v1/', include(regions_router.urls))
]
