from django.contrib import admin
from django.db.models import CharField, TextField
from django.forms import Textarea, TextInput

from .models import GeoObject


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
