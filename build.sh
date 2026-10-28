#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input

# Cargar el catalogo de pruebas si hay menos de 200 productos
PRODUCT_COUNT=$(python manage.py shell -c "
from apps.catalogo.models import Producto
print(Producto.objects.count())
" | tail -n 1)

echo "Productos encontrados en PostgreSQL: $PRODUCT_COUNT"

if [ "$PRODUCT_COUNT" -lt 200 ]; then
    echo "Catalogo incompleto. Cargando fixture de pruebas..."
    python manage.py loaddata fixtures/datos_render.json
else
    echo "Catalogo existente. Se conserva sin recargar el fixture."
fi

# Superusuario opcional
if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ]; then
    python manage.py createsuperuser --no-input || true
fi
