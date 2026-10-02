"""Configuracion del storage de la media (fotos de producto, portada).

Vive aparte de `settings.py` para poder probarla con un entorno falso: la
configuracion se evalua una sola vez al importar settings, y un error aca
(un dominio que no llega, una opcion mal escrita) se nota recien cuando las
fotos dejan de verse en la tienda.
"""

LOCAL = {'BACKEND': 'django.core.files.storage.FileSystemStorage'}
S3_BACKEND = 'storages.backends.s3boto3.S3Boto3Storage'

# Un dia de cache: la mayoria de los nombres no se reutiliza (file_overwrite
# es False), pero borrar una foto y subir otra con el mismo nombre si lo
# reutiliza, y un `immutable` de un año dejaria la foto vieja en el navegador.
MEDIA_CACHE_CONTROL = 'public, max-age=86400'


def media_storage_config(mode, env):
    """Devuelve la entrada `STORAGES['default']` para `MEDIA_STORAGE=mode`.

    `env` es un `environ.Env` (o algo con la misma firma `env(nombre, default=)`).
    """
    if mode != 's3':
        return LOCAL
    return {
        'BACKEND': S3_BACKEND,
        'OPTIONS': {
            'bucket_name': env('AWS_STORAGE_BUCKET_NAME'),
            'access_key': env('AWS_ACCESS_KEY_ID'),
            'secret_key': env('AWS_SECRET_ACCESS_KEY'),
            # R2 y compatibles necesitan endpoint propio; en S3 puro se omite.
            'endpoint_url': env('AWS_S3_ENDPOINT_URL', default=None),
            'region_name': env('AWS_S3_REGION_NAME', default='auto'),
            # Dominio publico de las fotos (p. ej. media.piedrasdelrayadito.cl),
            # sin esquema ni slash final. En R2 es obligatorio: el endpoint S3
            # exige firma, asi que sin dominio propio las URLs de las fotos no
            # abren (ver rayadito.E004 en core/checks.py).
            'custom_domain': env('AWS_S3_CUSTOM_DOMAIN', default=None),
            'querystring_auth': False,
            'file_overwrite': False,
            'object_parameters': {'CacheControl': MEDIA_CACHE_CONTROL},
        },
    }
