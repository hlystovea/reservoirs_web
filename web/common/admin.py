import csv
from django.contrib import admin
from django.db.models import CharField, TextField
from django.forms import Textarea, TextInput
from django.http import HttpResponse

from .models import Region


class MixinAdmin(admin.ModelAdmin):
    empty_value_display = '-пусто-'
    formfield_overrides = {
        CharField: {'widget': TextInput(attrs={'size': 80})},
        TextField: {'widget': Textarea(attrs={'rows': 8, 'cols': 80})},
    }


class ExportCsvMixin(admin.ModelAdmin):
    def export_as_csv(self, request, queryset):

        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={meta}.csv'
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = 'Сохранить выбранные в csv-файл'


@admin.register(Region)
class RegionAdmin(MixinAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
