"""
Context processor que hace disponible la configuracion global del sitio
(telefono, correo, redes sociales, WhatsApp, etc.) en TODAS las plantillas
como la variable `config_sitio`.
"""
from django.conf import settings

from .models import ConfiguracionSitio


def configuracion_sitio(request):
    return {
        'config_sitio': ConfiguracionSitio.get_solo(),
        'show_whatsapp_float': settings.SHOW_WHATSAPP_FLOAT,
    }
