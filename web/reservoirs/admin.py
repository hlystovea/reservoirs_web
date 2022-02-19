from django.contrib import admin
from django.db.models import CharField, TextField
from django.forms import Textarea, TextInput

from .models import Reservoir, WaterSituation


class MixinAdmin(admin.ModelAdmin):
    empty_value_display = '-пусто-'
    formfield_overrides = {
        CharField: {'widget': TextInput(attrs={'size': 80})},
        TextField: {'widget': Textarea(attrs={'rows': 8, 'cols': 80})},
    }

'''
class WaterSituationYearFilter(admin.SimpleListFilter):
    title = 'год'
    parameter_name = 'year'

    def lookups(self, request, model_admin):
        dates = WaterSituation.objects.dates('date', 'year')
        return [(d.year, d.year) for d in dates]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(date__year=self.value())
        return queryset


@admin.register(Reservoir)
class ReservoirAdmin(MixinAdmin):
    list_display = ('id', 'name', 'force_level', 'normal_level', 'dead_level',
                    'useful_volume', 'full_volume', 'area', 'region')
    search_fields = ('name', 'slug')
    list_filter = ('region__name', )
    prepopulated_fields = {'slug': ('name',)}


@admin.register(WaterSituation)
class WaterSituationAdmin(MixinAdmin):
    list_display = ('id', 'reservoir_id', 'date', 'level', 'free_capacity',
                    'inflow', 'outflow', 'spillway')
    search_fields = ('reservoir_id', )
    list_filter = ('reservoir_id__name', WaterSituationYearFilter)
'''