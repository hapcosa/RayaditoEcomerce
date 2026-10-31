from django.contrib import admin

from .models import HeroImage, HomepageSettings


@admin.register(HeroImage)
class HeroImageAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'position', 'is_active', 'date_created']
    list_editable = ['position', 'is_active']
    list_filter = ['is_active']


@admin.register(HomepageSettings)
class HomepageSettingsAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'hero_max_photos']
