from django.contrib import admin

from .models import Suggestion


class SuggestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'kind', 'name', 'email', 'status', 'created_at')
    list_display_links = ('id', 'kind')
    list_filter = ('kind', 'status', 'created_at')
    list_editable = ('status',)
    search_fields = ('name', 'email', 'message')
    # El contenido lo escribe el visitante; el staff solo modera el estado.
    readonly_fields = ('name', 'email', 'kind', 'message', 'user', 'created_at')
    list_per_page = 25


admin.site.register(Suggestion, SuggestionAdmin)
