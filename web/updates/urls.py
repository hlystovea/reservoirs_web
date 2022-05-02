from django.urls import path

from updates.views import UpdateList

app_name = 'updates'

urlpatterns = [
    path('updates', UpdateList.as_view(), name='update-list'),
]
