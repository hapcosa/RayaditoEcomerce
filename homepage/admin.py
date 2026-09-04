from django.contrib import admin

from .models import HeroImage


@admin.register(HeroImage)
class HeroImageAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'position', 'is_active', 'date_created']
    list_editable = ['position', 'is_active']
    list_filter = ['is_active']
