from django.contrib import admin
from django.db.models import CharField, TextField
from django.forms import Textarea, TextInput

from common.admin import ExportCsvMixin
from .models import Reservoir, WaterSituation


class MixinAdmin(admin.ModelAdmin):
    empty_value_display = '-пусто-'
    formfield_overrides = {
        CharField: {'widget': TextInput(attrs={'size': 80})},
        TextField: {'widget': Textarea(attrs={'rows': 8, 'cols': 80})},
    }


@admin.register(Reservoir)
class ReservoirAdmin(MixinAdmin):
    list_display = ('id', 'name', 'force_level', 'normal_level', 'dead_level',
                    'useful_volume', 'full_volume', 'area', 'max_depth')
    search_fields = ('name', 'slug')
    list_filter = ('region__name', )
    prepopulated_fields = {'slug': ('name',)}


@admin.register(WaterSituation)
class WaterSituationAdmin(MixinAdmin, ExportCsvMixin):
    list_display = ('id', 'reservoir_name', 'date', 'level', 'free_capacity',
                    'inflow', 'outflow', 'spillway')
    list_filter = ('reservoir__name', )
    date_hierarchy = 'date'
    actions = ['export_as_csv']

    @admin.display(description='Наименование вдхр.')
    def reservoir_name(self, obj):
        return obj.reservoir.name
