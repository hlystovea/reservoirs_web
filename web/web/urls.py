from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from core.views import IndexPageView


urlpatterns = [
    path('', IndexPageView.as_view(), name='index'),
    path('admin/', admin.site.urls),
    path('api/', include('reservoirs.urls', namespace='reservoirs')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # noqa (E501)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)  # noqa (E501)
