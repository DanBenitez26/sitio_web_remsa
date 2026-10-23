"""
Logica de negocio de cotizaciones: creacion de la solicitud a partir del
carrito en sesion, y envio de correos de notificacion/confirmacion.
Mantiene las vistas (views.py) delgadas.
"""
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from apps.catalogo.models import Producto
from apps.core.models import ConfiguracionSitio
from .models import SolicitudCotizacion, ItemCotizacion

logger = logging.getLogger(__name__)


def crear_solicitud_desde_carrito(cliente, mensaje, carrito, ip_origen=None):
    """
    carrito: dict {producto_id: cantidad} tomado de request.session.
    Crea la SolicitudCotizacion y sus ItemCotizacion asociados.
    """
    solicitud = SolicitudCotizacion.objects.create(
        cliente=cliente, mensaje=mensaje, ip_origen=ip_origen
    )
    items_creados = []
    for producto_id, cantidad in carrito.items():
        try:
            producto = Producto.objects.get(pk=producto_id, activo=True)
        except Producto.DoesNotExist:
            continue
        item = ItemCotizacion.objects.create(
            solicitud=solicitud, producto=producto, cantidad=max(1, int(cantidad))
        )
        items_creados.append(item)
    return solicitud, items_creados


def notificar_nueva_solicitud(solicitud):
    """Envia correo al area comercial y confirmacion al cliente. No detiene el flujo si falla el SMTP."""
    try:
        contexto = {'solicitud': solicitud, 'cliente': solicitud.cliente, 'items': solicitud.items.select_related('producto')}
        configuracion = ConfiguracionSitio.get_solo()
        destinatario = configuracion.correo_notificaciones or settings.COMERCIAL_EMAIL
        cuerpo_comercial = render_to_string('cotizaciones/email/notificacion_comercial.txt', contexto)
        cuerpo_cliente = render_to_string('cotizaciones/email/confirmacion_cliente.txt', contexto)
    except Exception:
        logger.exception('No se pudieron preparar los correos de la solicitud %s', solicitud.folio)
        return

    try:
        enviados = send_mail(
            subject=f'Nueva solicitud de cotización {solicitud.folio}',
            message=cuerpo_comercial,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[destinatario],
            fail_silently=False,
        )
        if enviados != 1:
            logger.error('El backend no confirmó el correo comercial de la solicitud %s', solicitud.folio)
    except Exception:
        logger.exception('Error enviando la notificación comercial de la solicitud %s', solicitud.folio)

    try:
        send_mail(
            subject=f'Hemos recibido tu solicitud de cotización — {solicitud.folio}',
            message=cuerpo_cliente,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[solicitud.cliente.correo],
            fail_silently=False,
        )
    except Exception:
        logger.exception('Error enviando la confirmación al cliente de la solicitud %s', solicitud.folio)
