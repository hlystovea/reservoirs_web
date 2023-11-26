from django.urls import include, path
from rest_framework_nested import routers

from predictors.views import ForecastViewSet, PredictorsViewSet


app_name = 'predictors'

v1_predictors = routers.SimpleRouter()
v1_predictors.register(r'predictors', PredictorsViewSet, basename='predictor')

v1_forecasts = routers.NestedSimpleRouter(v1_predictors, r'predictors', lookup='predictor')  # noqa(E501)
v1_forecasts.register(r'forecast', ForecastViewSet, basename='forecast')

urlpatterns = [
    path('v1/', include(v1_predictors.urls)),
    path('v1/', include(v1_forecasts.urls)),
]
