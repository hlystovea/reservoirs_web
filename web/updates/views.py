from django.views.generic import ListView

from updates.models import Update


class UpdateList(ListView):
    paginate_by = 10
    model = Update

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.order_by('-pub_date')
