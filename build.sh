#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input

# Carga los datos reales solo si la BD está vacía (no pisa cambios hechos en Render)
python manage.py shell -c "
import sys
from apps.catalogo.models import Producto
sys.exit(0 if Producto.objects.exists() else 1)
" && echo "BD con datos: se omite loaddata" || {
  if [ -f fixtures/datos_render.json ]; then
    python manage.py loaddata fixtures/datos_render.json
  fi
}

# Superusuario opcional (define DJANGO_SUPERUSER_USERNAME/EMAIL/PASSWORD en Render)
if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ]; then
  python manage.py createsuperuser --no-input || true
fi
