from django.contrib import admin
from .models import (
    Attribute,
    AttributeValue,
    Product,
    ProductAttributeValue,
    ProductVariant,
    ProductVariantAttributeValue,
    Joyas,
    Piedras,
    GalleryProduct,
    Review,
)


class ProductAttributeValueInline(admin.TabularInline):
    model = ProductAttributeValue
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


class JoyasAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'product_type', 'status', 'compare_price', 'price', 'available_stock', 'sold',)
    list_display_links=('id', 'name',)
    list_filter = ('category', 'product_type', 'status')
    list_editable = ('compare_price','price', 'status', 'sold',)
    list_per_page = 25
class PiedrasAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'product_type', 'status', 'compare_price', 'price', 'available_stock', 'sold',)
    list_display_links=('id', 'name',)
    list_filter = ('category', 'product_type', 'status')
    list_editable = ('compare_price','price', 'status', 'sold',)
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


class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'product_type', 'status', 'price', 'available_stock', 'is_featured')
    list_display_links = ('id', 'name')
    list_filter = ('category', 'product_type', 'status', 'is_featured')
    list_editable = ('status', 'price', 'is_featured')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description', 'slug')
    inlines = [ProductAttributeValueInline, ProductVariantInline]
    list_per_page = 25


class AttributeValueInline(admin.TabularInline):
    model = AttributeValue
    extra = 1


class AttributeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'kind', 'unit', 'is_variant_option', 'sort_order')
    list_display_links = ('id', 'name')
    list_editable = ('kind', 'unit', 'is_variant_option', 'sort_order')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [AttributeValueInline]


class ProductVariantAttributeValueInline(admin.TabularInline):
    model = ProductVariantAttributeValue
    extra = 1


class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'sku', 'effective_price', 'stock', 'is_active')
    list_display_links = ('id', 'product')
    list_filter = ('is_active', 'product__product_type')
    list_editable = ('stock', 'is_active')
    inlines = [ProductVariantAttributeValueInline]


admin.site.register(Product, ProductAdmin)
admin.site.register(Joyas, JoyasAdmin)
admin.site.register(Piedras, PiedrasAdmin)
admin.site.register(GalleryProduct, Galleryproducts)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Attribute, AttributeAdmin)
admin.site.register(ProductVariant, ProductVariantAdmin)
