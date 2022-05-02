from django.contrib import admin

from updates.models import Update


@admin.register(Update)
class UpdateAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'pub_date')
    search_fields = ('text', )
    list_filter = ('pub_date', )
    date_hierarchy = 'pub_date'
    empty_value_display = '-'
