"""
Selector de settings: decide si cargar dev.py o prod.py según la variable
de entorno DJANGO_ENV definida en el archivo .env (por defecto: 'dev').
"""
import os
import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

DJANGO_ENV = env('DJANGO_ENV', default='dev')

if DJANGO_ENV == 'prod':
    from .prod import *  # noqa: F401,F403
else:
    from .dev import *  # noqa: F401,F403
