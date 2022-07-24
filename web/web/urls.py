from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from core.views import IndexPageView


schema_view = get_schema_view(
   openapi.Info(
      title='Reservoirs API',
      default_version='v1',
      description='Гидрологическая обстановка на водохранилищах ГЭС России',
      license=openapi.License(name='MIT License'),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)


urlpatterns = [
    path('', IndexPageView.as_view(), name='index'),
    path('admin/', admin.site.urls),
    path('api/', include('reservoirs.urls', namespace='reservoirs')),
    path('api/', include('common.urls', namespace='common')),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),  # noqa (E501)
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),  # noqa (E501)
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),  # noqa (E501)
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # noqa (E501)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)  # noqa (E501)
