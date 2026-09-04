from pathlib import Path
import os
import environ
from datetime import timedelta

# django-environ: lee variables desde el entorno y desde un archivo .env (no versionado).
env = environ.Env()
environ.Env.read_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
# En producción define SECRET_KEY en el entorno; el default es solo para desarrollo.
SECRET_KEY = env('SECRET_KEY', default='django-insecure-CHANGE-ME-set-SECRET_KEY-in-.env')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', default=False)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['127.0.0.1', 'localhost'])


# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

PROJECT_APPS = [
    'core',
    'user',
    'category',
    'product',
    'metaproduct',
    'carrito',
    'shipping',
    'orders',
    'user_profile',
    'payment',
    'suggestions',
    'wishlist',
    'homepage',
]

THIRD_PARTY_APPS = [
    'corsheaders',
    'rest_framework',
    'djoser',
    'social_django',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'django_ckeditor_5',
    'drf_spectacular',
]

INSTALLED_APPS = DJANGO_APPS + PROJECT_APPS + THIRD_PARTY_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Almacenamiento (API `STORAGES` de Django 4.2+; `STATICFILES_STORAGE` a secas
# quedo obsoleto). La media va al disco del servidor salvo que se configure un
# bucket: hoy las fotos de producto viven en el PC, asi que si se pierde ese
# disco se pierden. Poner MEDIA_STORAGE=s3 las manda a S3 / Cloudflare R2 sin
# tocar codigo (django-storages ya esta en requirements).
MEDIA_STORAGE = env('MEDIA_STORAGE', default='local')

if MEDIA_STORAGE == 's3':
    _default_storage = {
        'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
        'OPTIONS': {
            'bucket_name': env('AWS_STORAGE_BUCKET_NAME'),
            'access_key': env('AWS_ACCESS_KEY_ID'),
            'secret_key': env('AWS_SECRET_ACCESS_KEY'),
            # R2 y compatibles necesitan endpoint propio; en S3 puro se omite.
            'endpoint_url': env('AWS_S3_ENDPOINT_URL', default=None),
            'region_name': env('AWS_S3_REGION_NAME', default='auto'),
            'querystring_auth': False,
            'file_overwrite': False,
        },
    }
else:
    _default_storage = {'BACKEND': 'django.core.files.storage.FileSystemStorage'}

STORAGES = {
    'default': _default_storage,
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}
ROOT_URLCONF = 'core.urls'
SOCIAL_AUTH_JSONFIELD_ENABLED = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Sin el `dist/` del SPA de Vite: la tienda la sirve Next.js.
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database — PostgreSQL vía psycopg3. Config por entorno con defaults de desarrollo
# que calzan con docker-compose.yml (ver .env.example).
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='piedrasrayadito'),
        'USER': env('DB_USER', default='rayadito'),
        'PASSWORD': env('DB_PASSWORD', default='rayadito'),
        'HOST': env('DB_HOST', default='127.0.0.1'),
        'PORT': env('DB_PORT', default='15432'),
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True


# Static & media files
STATIC_ROOT = os.path.join(BASE_DIR, 'assets')
STATIC_URL = '/assets/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'public')
MEDIA_URL = '/public/'

# Los estaticos que quedan son los del admin de Django y los de DRF: el build
# del front vivia en `dist/assets` y se retiro junto con el SPA de Vite.
STATICFILES_DIRS = []

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# CKEditor 5 (editor de texto enriquecido del admin)
customColorPalette = [
    {'color': 'hsl(4, 90%, 58%)', 'label': 'Red'},
    {'color': 'hsl(340, 82%, 52%)', 'label': 'Pink'},
    {'color': 'hsl(291, 64%, 42%)', 'label': 'Purple'},
    {'color': 'hsl(262, 52%, 47%)', 'label': 'Deep Purple'},
    {'color': 'hsl(231, 48%, 48%)', 'label': 'Indigo'},
    {'color': 'hsl(207, 90%, 54%)', 'label': 'Blue'},
]

CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': ['heading', '|', 'bold', 'italic', 'link',
                    'bulletedList', 'numberedList', 'blockQuote', 'imageUpload', ],
    },
    'extends': {
        'blockToolbar': [
            'paragraph', 'heading1', 'heading2', 'heading3',
            '|',
            'bulletedList', 'numberedList',
            '|',
            'blockQuote',
        ],
        'toolbar': ['heading', '|', 'outdent', 'indent', '|', 'bold', 'italic', 'link', 'underline', 'strikethrough',
                    'code', 'subscript', 'superscript', 'highlight', '|', 'codeBlock', 'sourceEditing', 'insertImage',
                    'bulletedList', 'numberedList', 'todoList', '|', 'blockQuote', 'imageUpload', '|',
                    'fontSize', 'fontFamily', 'fontColor', 'fontBackgroundColor', 'mediaEmbed', 'removeFormat',
                    'insertTable', ],
        'image': {
            'toolbar': ['imageTextAlternative', '|', 'imageStyle:alignLeft',
                        'imageStyle:alignRight', 'imageStyle:alignCenter', 'imageStyle:side', '|'],
            'styles': ['full', 'side', 'alignLeft', 'alignRight', 'alignCenter'],
        },
        'table': {
            'contentToolbar': ['tableColumn', 'tableRow', 'mergeTableCells',
                               'tableProperties', 'tableCellProperties'],
            'tableProperties': {
                'borderColors': customColorPalette,
                'backgroundColors': customColorPalette,
            },
            'tableCellProperties': {
                'borderColors': customColorPalette,
                'backgroundColors': customColorPalette,
            },
        },
        'heading': {
            'options': [
                {'model': 'paragraph', 'title': 'Paragraph', 'class': 'ck-heading_paragraph'},
                {'model': 'heading1', 'view': 'h1', 'title': 'Heading 1', 'class': 'ck-heading_heading1'},
                {'model': 'heading2', 'view': 'h2', 'title': 'Heading 2', 'class': 'ck-heading_heading2'},
                {'model': 'heading3', 'view': 'h3', 'title': 'Heading 3', 'class': 'ck-heading_heading3'},
            ],
        },
    },
    'list': {
        'properties': {
            'styles': 'true',
            'startIndex': 'true',
            'reversed': 'true',
        },
    },
}
CKEDITOR_5_FILE_UPLOAD_PERMISSION = "staff"


# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 12,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # Rate limiting. **Solo por scope, a proposito.** Un throttle global por IP
    # seria contraproducente: Next.js renderiza en el servidor, asi que todas
    # las peticiones del catalogo llegan desde la IP del propio servidor y un
    # limite `anon` las contaria juntas, tumbando el sitio con poco trafico.
    # Los scopes se aplican en vistas que sí llama el navegador del cliente.
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        # Crear una preferencia de pago golpea a MercadoPago y crea una orden.
        'payment': env('THROTTLE_PAYMENT', default='10/min'),
        # Formularios publicos sin auth: el buzon y las reseñas.
        'suggestions': env('THROTTLE_SUGGESTIONS', default='5/min'),
        'reviews': env('THROTTLE_REVIEWS', default='20/min'),
    },
    # Detras del tunel la IP del cliente llega en X-Forwarded-For. Sin esto DRF
    # usaria REMOTE_ADDR —el proxy— y todos los visitantes compartirian cuota.
    # Cantidad de proxies que agregan a esa cabecera: `cloudflared` mas los de
    # Cloudflare. Verificar el valor real contra el sitio desplegado.
    'NUM_PROXIES': env.int('NUM_PROXIES', default=None),
}

# El throttling de DRF necesita cache. Con varios workers de gunicorn cada uno
# tiene su propia LocMemCache, asi que el limite efectivo se multiplica por la
# cantidad de workers: suficiente como freno grueso, no como cuota exacta. Si
# alguna vez hace falta precisión, apuntar CACHE_URL a un Redis.
CACHES = {
    'default': env.cache('CACHE_URL', default='locmemcache://'),
}

# OpenAPI (drf-spectacular). Esquema en /api/schema, docs en /api/docs.
SPECTACULAR_SETTINGS = {
    'TITLE': 'Piedras Rayadito API',
    'DESCRIPTION': 'API del ecommerce artesanal de joyería y lapidación de '
                   'piedras de Chiloé. Dinero en entero CLP.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}


# Auth backends (social + local)
AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.facebook.FacebookOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = env('GOOGLE_CLIENT_KEY', default='')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = env('GOOGLE_CLIENT_SECRET', default='')
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
]
SOCIAL_AUTH_GOOGLE_OAUTH2_EXTRA_DATA = ["first_name", "last_name"]

# Facebook Login (Meta). Requiere una app de Meta con Facebook Login habilitado;
# sin credenciales el proveedor queda inactivo (el botón fallará al iniciar).
SOCIAL_AUTH_FACEBOOK_KEY = env('FACEBOOK_CLIENT_KEY', default='')
SOCIAL_AUTH_FACEBOOK_SECRET = env('FACEBOOK_CLIENT_SECRET', default='')
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
    'fields': 'id, email, first_name, last_name',
}

SIMPLE_JWT = {
    'AUTH_HEADER_TYPES': ('JWT', ),
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=10080),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKEN': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_TOKEN_CLASSES': (
        'rest_framework_simplejwt.tokens.AccessToken',
    ),
}

DJOSER = {
    'LOGIN_FIELD': 'email',
    'USER_CREATE_PASSWORD_RETYPE': True,
    'USERNAME_CHANGED_EMAIL_CONFIRMATION': True,
    'PASSWORD_CHANGED_EMAIL_CONFIRMATION': True,
    'SEND_CONFIRMATION_EMAIL': True,
    'SET_USERNAME_RETYPE': True,
    'PASSWORD_RESET_CONFIRM_URL': 'password/reset/confirm/{uid}/{token}',
    'SET_PASSWORD_RETYPE': True,
    'PASSWORD_RESET_CONFIRM_RETYPE': True,
    'USERNAME_RESET_CONFIRM_URL': 'email/reset/confirm/{uid}/{token}',
    'ACTIVATION_URL': 'activate/{uid}/{token}',
    'SEND_ACTIVATION_EMAIL': True,
    'SOCIAL_AUTH_TOKEN_STRATEGY': 'djoser.social.token.jwt.TokenStrategy',
    'SOCIAL_AUTH_ALLOWED_REDIRECT_URIS': env.list(
        'SOCIAL_AUTH_ALLOWED_REDIRECT_URIS',
        default=[
            'http://127.0.0.1:5173/',
            'http://localhost:8000/facebook',
            # Callback del front Next.js (login social → intercambio de code).
            'http://localhost:3000/auth/social/callback',
            'http://127.0.0.1:3000/auth/social/callback',
        ],
    ),
    'SERIALIZERS': {
        'user_create': 'user.serializer.UserCreateSerializer',
        'user': 'user.serializer.CurrentUserSerializer',
        'current_user': 'user.serializer.CurrentUserSerializer',
        'user_delete': 'djoser.serializers.UserDeleteSerializer',
    },
}

AUTH_USER_MODEL = 'user.UserAccount'


# CORS / CSRF — orígenes explícitos por entorno (nunca ALLOW_ALL con credenciales).
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
])
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
])


# Email — consola en desarrollo; SMTP por entorno en producción.
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='')
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
DEFAULT_FROM_EMAIL = env(
    'DEFAULT_FROM_EMAIL',
    default='Piedras Rayadito - Taller de joyeria y lapidacion <no-reply@piedrasdelrayadito.cl>',
)


# Detrás del túnel de Cloudflare, `cloudflared` habla HTTP plano contra este
# proceso y el TLS lo termina Cloudflare. Confiar en el Host reenviado hace que
# Django construya URLs absolutas con el dominio público y no con `localhost`:
# de ahí sale, entre otras, la `notification_url` del webhook de MercadoPago.
USE_X_FORWARDED_HOST = env.bool('USE_X_FORWARDED_HOST', default=False)

# Sentry. Opt-in: sin `SENTRY_DSN` no se inicializa nada, asi que en dev y en
# los tests el modulo ni se importa.
SENTRY_DSN = env('SENTRY_DSN', default='')
if SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=env('SENTRY_ENVIRONMENT', default='production'),
        # Muestreo de performance: 0 por defecto para no gastar cuota; subirlo
        # a mano si hace falta perfilar.
        traces_sample_rate=env.float('SENTRY_TRACES_SAMPLE_RATE', default=0.0),
        # No mandar datos personales (emails, direcciones) a un tercero.
        send_default_pii=False,
    )


# Hardening de producción (solo cuando DEBUG=False).
if not DEBUG:
    # El redirect a HTTPS lo resuelve Cloudflare antes de llegar acá; junto con
    # SECURE_PROXY_SSL_HEADER esto evita el loop de redirecciones.
    SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=0)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True


# Logging. El LOGGING por defecto de Django filtra la consola con
# `require_debug_true`: con DEBUG=False los 500 no dejan rastro en ningun lado
# y los errores de produccion pasan en silencio. Acá mandamos todo a stderr,
# que es lo que captura gunicorn (y systemd/journald cuando corresponda).
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'estandar': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'consola': {
            'class': 'logging.StreamHandler',
            'formatter': 'estandar',
        },
    },
    'root': {
        'handlers': ['consola'],
        'level': env('LOG_LEVEL', default='INFO'),
    },
    'loggers': {
        # Los 500 salen por acá con su traceback.
        'django.request': {
            'handlers': ['consola'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
