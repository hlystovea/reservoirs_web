from django.contrib import admin
from django.db.models import CharField, TextField
from django.forms import Textarea, TextInput

from .models import Region


class MixinAdmin(admin.ModelAdmin):
    empty_value_display = '-пусто-'
    formfield_overrides = {
        CharField: {'widget': TextInput(attrs={'size': 80})},
        TextField: {'widget': Textarea(attrs={'rows': 8, 'cols': 80})},
    }


@admin.register(Region)
class RegionAdmin(MixinAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
