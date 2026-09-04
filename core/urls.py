from django.contrib import admin
from django.urls import path, re_path, include
from django.views.static import serve
from django.conf import settings
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
urlpatterns = [
    # OpenAPI: esquema crudo + Swagger UI + ReDoc.
    path('api/schema', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path("auth/", include('djoser.urls')),
    path("auth/", include('djoser.urls.jwt')),
    path("auth/", include('djoser.social.urls')),
    path('', include('social_django.urls')),
    path('api/category/', include('category.urls')),
    path('api/product/', include('product.urls')),
    path('api/products/', include('product.generic_urls')),
    path('api/attributes/', include('product.attribute_urls')),
    path('api/reviews/', include('product.review_urls')),
    path('api/cart/', include('carrito.urls')),
    path('api/shipp/', include('shipping.urls')),
    path('api/profile/', include('user_profile.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/payment/', include('payment.urls')),
    path('api/suggestions/', include('suggestions.urls')),
    path('api/wishlist/', include('wishlist.urls')),
    path('api/homepage/', include('homepage.urls')),
    # API de escritura para staff (app admin Expo, Fase 5).
    path('api/admin/', include('product.admin_urls')),
    path('api/admin/', include('orders.admin_urls')),
    path('api/admin/', include('homepage.admin_urls')),
    path("admin/", admin.site.urls),
    path("ckeditor5/", include('django_ckeditor_5.urls')),
    path("api/meta/", include('metaproduct.urls')),
    
]

# Media (fotos de producto). `static()` solo funciona con DEBUG=True, asi que
# tras el cutover las fotos desaparecian en produccion: el SPA ya no esta y no
# hay nginx delante, solo el tunel, que no sabe servir archivos. Hasta que la
# media viva en object storage (Fase 7) la sirve este proceso. Cloudflare cachea
# por delante, asi que el costo real es bajo.
urlpatterns += [
    re_path(r'^%s(?P<path>.*)$' % settings.MEDIA_URL.lstrip('/'), serve,
            {'document_root': settings.MEDIA_ROOT}),
]

# La tienda publica la sirve Next.js (`web/`), no Django. El proxy que termina
# el tunel manda `/api/`, `/auth/`, `/admin/`, `/ckeditor5/` y `MEDIA_URL` aca y
# todo lo demas a Next, asi que una ruta desconocida en este proceso es un error
# de backend y responde JSON, no el HTML del SPA que Django servia antes.
handler404 = 'core.views.page_not_found'
