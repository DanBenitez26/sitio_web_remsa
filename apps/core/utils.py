"""
Utilidades compartidas: rate limiting simple basado en cache/sesion para
formularios publicos (cotizacion y contacto), sin dependencias externas.
"""
from django.conf import settings
from django.core.cache import cache


def obtener_ip_cliente(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def excede_limite_envios(request, clave_formulario):
    """
    Antispam simple: limita cuantos envios puede hacer una misma IP para un
    formulario dado dentro de una ventana de tiempo (settings.FORM_RATE_LIMIT_*).
    Retorna True si ya alcanzo el limite (debe bloquearse el envio).
    """
    ip = obtener_ip_cliente(request) or 'sin-ip'
    cache_key = f'rate_limit:{clave_formulario}:{ip}'
    intentos = cache.get(cache_key, 0)
    limite = getattr(settings, 'FORM_RATE_LIMIT_MAX', 5)
    ventana = getattr(settings, 'FORM_RATE_LIMIT_WINDOW_SECONDS', 600)
    if intentos >= limite:
        return True
    cache.set(cache_key, intentos + 1, timeout=ventana)
    return False
