"""
Settings de DESARROLLO.
Uso: DJANGO_ENV=dev en el .env (o por defecto si no se define).
Base de datos: SQLite (cero configuración, ideal para Windows 11 / equipo local).
"""
from .base import *  # noqa: F401,F403
from .base import env, BASE_DIR

DEBUG = True

ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['127.0.0.1', 'localhost'])

if env('DB_ENGINE', default='sqlite').lower() == 'postgresql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('PGDATABASE', default='remsa_db'),
            'USER': env('PGUSER', default='postgres'),
            'PASSWORD': env('PGPASSWORD', default='root'),
            'HOST': env('PGHOST', default='127.0.0.1'),
            'PORT': env('PGPORT', default='5432'),
        }
    }
else:
    DATABASES = { 
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }



#DATABASES = {
#    'default': {
#       'ENGINE': 'django.db.backends.sqlite3',
#
#        'NAME': BASE_DIR / 'db.sqlite3',
#  }
#}

# En desarrollo es útil ver los correos en consola aunque el .env no lo especifique
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')

# Logging simple a consola en desarrollo
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {'handlers': ['console'], 'level': 'INFO'},
}
