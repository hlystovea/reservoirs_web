from django.contrib import admin
from django.db.models import CharField, TextField
from django.forms import Textarea, TextInput

from .models import GeoObject, Weather


class MixinAdmin(admin.ModelAdmin):
    empty_value_display = '-'
    formfield_overrides = {
        CharField: {'widget': TextInput(attrs={'size': 80})},
        TextField: {'widget': Textarea(attrs={'rows': 8, 'cols': 80})},
    }


@admin.register(GeoObject)
class GeoObjectAdmin(MixinAdmin):
    list_display = ('id', 'name', 'gismeteo_id', 'latitude', 'longitude')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Weather)
class WeatherAdmin(MixinAdmin):
    list_display = ('id', 'date', 'object_name', 'temp', 'pressure',
                    'humidity', 'cloudiness', 'wind_speed',
                    'wind_direction', 'precipitation', 'is_observable')
    list_filter = ('geo_object__name', 'wind_direction', 'is_observable')
    date_hierarchy = 'date'

    @admin.display(description='Название объекта')
    def object_name(self, obj):
        return obj.geo_object.name
