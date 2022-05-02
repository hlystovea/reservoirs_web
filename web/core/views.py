from django.views.generic.base import TemplateView

from reservoirs.utils import get_date_before, get_earlist_date


class IndexPageView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['index'] = True
        context['default_date'] = get_date_before()
        context['earlist_date'] = get_earlist_date()
        return context


class AboutPageView(TemplateView):
    template_name = 'about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['about'] = True
        return context
