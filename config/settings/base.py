"""
Settings base compartidos por dev y prod.
No se usa directamente: Django carga dev.py o prod.py según DJANGO_ENV,
y ambos heredan de este archivo con `from .base import *`.
"""
from pathlib import Path
import environ

# BASE_DIR = raíz del proyecto (donde vive manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# django-environ: lee variables desde el archivo .env en la raíz del proyecto
env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('DJANGO_SECRET_KEY', default='clave-insegura-solo-para-desarrollo')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',

    # Terceros
    'rest_framework',
    'widget_tweaks',

    # Apps propias de REMSA
    'apps.core',
    'apps.catalogo',
    'apps.cotizaciones',
    'apps.contacto',
    'apps.paginas',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Context processor propio: inyecta ConfiguracionSitio en todas las plantillas
                'apps.core.context_processors.configuracion_sitio',
                'apps.cotizaciones.context_processors.carrito_info',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Merida'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
# NOTA: STATICFILES_STORAGE con manifest (WhiteNoise comprimido) se define
# SOLO en prod.py, ya que requiere haber corrido collectstatic previamente.
# En desarrollo se usa el almacenamiento simple por defecto de Django.

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



# === Correo ===
EMAIL_BACKEND = env(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.smtp.EmailBackend'
)
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='kxsnkkrobupljxep')
DEFAULT_FROM_EMAIL = env(
    'DEFAULT_FROM_EMAIL',
    default='REMSA Plásticos <danbenitez448@gmail.com>'
)
COMERCIAL_EMAIL = env(
    'COMERCIAL_EMAIL',
    default='danbenitez448@gmail.com'
)


# === Correo (compartido; los valores vienen del .env) ===
#EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
#EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
#EMAIL_PORT = env.int('EMAIL_PORT', default=587)
#EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
#EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
#EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
#DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='REMSA Plásticos <danbenitez448@gmail.com>')
#COMERCIAL_EMAIL = env('COMERCIAL_EMAIL', default='danbenitez448@gmail.com')


RECAPTCHA_SITE_KEY = env('RECAPTCHA_SITE_KEY', default='')
RECAPTCHA_SECRET_KEY = env('RECAPTCHA_SECRET_KEY', default='')

SITE_NAME = env('SITE_NAME', default='REMSA Plásticos')
SHOW_WHATSAPP_FLOAT = env.bool('SHOW_WHATSAPP_FLOAT', default=False)

# === Django REST Framework ===
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # se restringe por vista donde aplique
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# === Rate limiting simple para formularios públicos (cotización/contacto) ===
# Umbral de envíos por IP en la ventana de tiempo indicada (usado en apps.core.utils)
FORM_RATE_LIMIT_MAX = 5
FORM_RATE_LIMIT_WINDOW_SECONDS = 600  # 10 minutos

LOGIN_URL = '/admin/login/'

# Mapea el tag 'error' de django.contrib.messages a la clase 'danger' de Bootstrap
from django.contrib.messages import constants as message_constants  # noqa: E402
MESSAGE_TAGS = {
    message_constants.ERROR: 'danger',
}
