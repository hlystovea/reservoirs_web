from django.contrib import admin
from django.urls import path

from core.views import IndexPageView


urlpatterns = [
    path('', IndexPageView.as_view(), name='index'),
    path('admin/', admin.site.urls),
]
