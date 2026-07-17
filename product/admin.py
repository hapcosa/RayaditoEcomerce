from django.contrib import admin
from .models import Product, Joyas, Piedras, GalleryProduct, Review

class JoyasAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'compare_price', 'price', 'sold',)
    list_display_links=('id', 'name',)
    list_filter = ('category',)
    list_editable = ('compare_price','price', 'sold',)
    list_per_page = 25
class PiedrasAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'compare_price', 'price', 'sold',)
    list_display_links=('id', 'name',)
    list_filter = ('category',)
    list_editable = ('compare_price','price', 'sold',)
    list_per_page = 25
class Galleryproducts(admin.ModelAdmin):
    list_display =('id', 'product')
    list_display_links=('id', 'product')
    list_filter =('product',)
    list_per_page = 25


class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'user', 'rating', 'verified_purchase', 'approved', 'created_at')
    list_display_links = ('id', 'product')
    list_filter = ('approved', 'rating', 'verified_purchase')
    list_editable = ('approved',)
    search_fields = ('product__name', 'user__email', 'comment')
    list_per_page = 25


admin.site.register(Joyas, JoyasAdmin)
admin.site.register(Piedras, PiedrasAdmin)
admin.site.register(GalleryProduct, Galleryproducts)
admin.site.register(Review, ReviewAdmin)
