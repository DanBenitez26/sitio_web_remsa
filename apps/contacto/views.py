import logging
from smtplib import SMTPException

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.db import DatabaseError
from django.db.utils import OperationalError, ProgrammingError
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from apps.core.models import ConfiguracionSitio
from apps.core.utils import excede_limite_envios, obtener_ip_cliente
from .captcha import CaptchaConfigurationError, verificar_recaptcha
from urllib.parse import quote_plus

from django.core.mail import EmailMessage

from .forms import (
    ChatbotLeadForm,
    ContactoCentroamericaForm,
    ContactoForm,
    SolicitudCatalogoForm,
)
from .models import MensajeContacto

logger = logging.getLogger(__name__)


EMPRESA_CENTROAMERICA = 'Recipientes y Empaques de Centroamérica, S.A.'
DIRECCION_CENTROAMERICA = (
    'Parque Industrial Zeta la Unión, Km. 30.5 Carretera al Pacífico, '
    '1ª Avenida Lote 6, Amatitlán, Guatemala, C.A.'
)


def _contexto_centroamerica():
    consulta = quote_plus(f'{EMPRESA_CENTROAMERICA}, {DIRECCION_CENTROAMERICA}')
    site_key = getattr(settings, 'RECAPTCHA_SITE_KEY', '')
    secret_key = getattr(settings, 'RECAPTCHA_SECRET_KEY', '')
    return {
        'ca_empresa': EMPRESA_CENTROAMERICA,
        'ca_direccion': DIRECCION_CENTROAMERICA,
        'ca_mapa_embed_url': f'https://www.google.com/maps?q={consulta}&z=16&output=embed',
        'ca_mapa_url': f'https://www.google.com/maps/search/?api=1&query={consulta}',
        'ca_form': ContactoCentroamericaForm(),
        'recaptcha_enabled': bool(site_key and secret_key),
        'recaptcha_site_key': site_key,
    }


@csrf_protect
@require_POST
def contacto_centroamerica(request):
    def error(message, status, errors=None):
        body = {'success': False, 'message': message}
        if errors:
            body['errors'] = errors
        return JsonResponse(body, status=status)

    form = ContactoCentroamericaForm(request.POST)
    if not form.is_valid():
        return error(
            'Revisa los campos marcados e inténtalo de nuevo.',
            400,
            form.errors.get_json_data(),
        )

    if excede_limite_envios(request, 'contacto_centroamerica'):
        return error('Has enviado demasiados mensajes en poco tiempo. Intenta de nuevo más tarde.', 429)

    try:
        captcha_valid = verificar_recaptcha(request.POST.get('g-recaptcha-response', ''), request)
    except CaptchaConfigurationError:
        logger.exception('Configuración CAPTCHA incompleta en contacto Centroamérica.')
        return error('No se pudo validar el formulario. Intenta más tarde.', 503)
    if not captcha_valid:
        return error('Completa la validación de seguridad e inténtalo de nuevo.', 400)

    try:
        destinatario = (
            ConfiguracionSitio.get_solo().correo_notificaciones
            or settings.COMERCIAL_EMAIL
        )
    except (OperationalError, ProgrammingError):
        logger.exception('No se pudo leer el destinatario de contacto Centroamérica.')
        return error('No pudimos procesar tu mensaje en este momento. Intenta más tarde.', 503)
    if not destinatario:
        logger.error('No hay destinatario configurado para contacto Centroamérica.')
        return error('No pudimos procesar tu mensaje en este momento. Intenta más tarde.', 503)

    datos = form.cleaned_data
    cuerpo = (
        f'Nueva consulta para {EMPRESA_CENTROAMERICA}\n\n'
        f"Nombre: {datos['nombre']}\n"
        f"Empresa: {datos['empresa']}\n"
        f"Correo: {datos['correo']}\n"
        f"Teléfono: {datos['telefono']}\n"
        f"Asunto: {datos['asunto']}\n\n"
        f"Mensaje:\n{datos['mensaje']}\n\n"
        f'Fecha y hora de recepción: {timezone.localtime().strftime("%d/%m/%Y %H:%M %Z")}'
    )
    asunto = ' '.join(f"[Centroamérica] Nueva consulta: {datos['asunto']}".split())
    try:
        enviados = EmailMessage(
            subject=asunto,
            body=cuerpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[destinatario],
            reply_to=[datos['correo']],
        ).send(fail_silently=False)
    except (SMTPException, OSError, ValueError):
        logger.exception('Falló el envío de la consulta de contacto Centroamérica.')
        return error('No pudimos enviar tu mensaje. Inténtalo nuevamente en unos minutos.', 502)
    if enviados != 1:
        return error('No pudimos enviar tu mensaje. Inténtalo nuevamente en unos minutos.', 502)

    return JsonResponse({
        'success': True,
        'message': '¡Gracias! Tu mensaje fue enviado correctamente. Te responderemos a la brevedad.',
    })


def contacto(request):
    if request.method == 'POST':
        form = ContactoForm(request.POST)

        if excede_limite_envios(request, 'contacto'):
            messages.error(
                request,
                'Has enviado demasiados mensajes en poco tiempo. Intenta de nuevo más tarde.'
            )

        elif form.is_valid():
            mensaje = form.save(commit=False)
            mensaje.ip_origen = obtener_ip_cliente(request)
            mensaje.save()

            configuracion = ConfiguracionSitio.get_solo()
            destinatario = (
                configuracion.correo_notificaciones
                or settings.COMERCIAL_EMAIL
            )

            try:
                enviados = send_mail(
                    subject=f'Nuevo mensaje de contacto: {mensaje.asunto or "Sin asunto"}',
                    message=(
                        f'Nombre: {mensaje.nombre}\n'
                        f'Correo: {mensaje.correo}\n'
                        f'Teléfono: {mensaje.telefono}\n\n'
                        f'{mensaje.mensaje}'
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[destinatario],
                    fail_silently=False,
                )

                if enviados == 1:
                    messages.success(
                        request,
                        'Tu mensaje fue enviado correctamente. Te contactaremos a la brevedad.'
                    )
                else:
                    messages.error(
                        request,
                        'El mensaje fue recibido, pero no se pudo enviar la notificación por correo.'
                    )

            except Exception:
                logger.exception(
                    'Error enviando la notificación del mensaje de contacto %s.',
                    mensaje.pk
                )

                messages.error(
                    request,
                    'Recibimos tu mensaje, pero ocurrió un problema al enviar la notificación. Intenta nuevamente.'
                )

            return redirect('contacto:contacto')

    else:
        form = ContactoForm()

    return render(request, 'contacto/contacto.html', {
        **_contexto_centroamerica(),
        'form': form,
        'meta_title': 'Contacto | REMSA Plásticos',
        'meta_description': (
            'Ponte en contacto con REMSA Plásticos para solicitar '
            'información o una cotización.'
        ),
    })


@csrf_protect
@require_POST
def chatbot_lead(request):
    form = ChatbotLeadForm(request.POST)
    if not form.is_valid():
        return JsonResponse(
            {
                'success': False,
                'message': 'Revisa tus datos e inténtalo de nuevo.',
                'errors': form.errors.get_json_data(),
            },
            status=400,
        )

    submission_id = str(form.cleaned_data['submission_id'])
    if request.session.get('chatbot_completed_submission') == submission_id:
        return JsonResponse({
            'success': True,
            'message': (
                '¡Gracias por contactar a REMSA Plásticos! Hemos recibido tus datos. '
                'Un asesor comercial dará seguimiento a tu solicitud.'
            ),
        })

    if excede_limite_envios(request, 'chatbot'):
        return JsonResponse(
            {
                'success': False,
                'message': 'Recibimos varias solicitudes. Espera un momento e inténtalo de nuevo.',
            },
            status=429,
        )

    data = form.cleaned_data
    message_parts = []
    if data['producto']:
        message_parts.append(f"Producto de interés: {data['producto']}")
    if data['mensaje']:
        message_parts.append(data['mensaje'])

    try:
        lead = MensajeContacto.objects.create(
            nombre=data['nombre'],
            empresa=data['empresa'],
            correo=data['correo'],
            telefono=data['telefono'],
            asunto='Solicitud de contacto desde el chatbot',
            mensaje='\n\n'.join(message_parts) or 'Solicitud de seguimiento comercial.',
            ip_origen=obtener_ip_cliente(request),
        )
    except DatabaseError:
        logger.exception('No se pudo guardar la solicitud de contacto del chatbot.')
        return JsonResponse(
            {
                'success': False,
                'message': 'No pudimos guardar tu solicitud. Inténtalo nuevamente en unos minutos.',
            },
            status=500,
        )

    request.session['chatbot_completed_submission'] = submission_id
    notification_sent = False
    if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
        logger.error(
            'La solicitud del chatbot %s se guardó, pero EMAIL_BACKEND está configurado en consola.',
            lead.pk,
        )
    else:
        try:
            configuracion = ConfiguracionSitio.get_solo()
            destinatario = (
                configuracion.correo_notificaciones
                or settings.COMERCIAL_EMAIL
            )
        except DatabaseError:
            logger.exception(
                'La solicitud del chatbot %s se guardó, pero no se pudo leer el destinatario.',
                lead.pk,
            )
            destinatario = ''

        if not destinatario:
            logger.error(
                'La solicitud del chatbot %s se guardó, pero no hay destinatario comercial configurado.',
                lead.pk,
            )
        elif (
            settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend'
            and not settings.EMAIL_HOST
        ):
            logger.error(
                'La solicitud del chatbot %s se guardó, pero falta configurar EMAIL_HOST.',
                lead.pk,
            )
        else:
            try:
                notification_sent = send_mail(
                    subject='Nueva solicitud de contacto desde el chatbot REMSA',
                    message=(
                        'Nueva solicitud recibida desde el asistente comercial.\n\n'
                        f'Nombre: {lead.nombre}\n'
                        f'Empresa: {lead.empresa}\n'
                        f'Teléfono o WhatsApp: {lead.telefono}\n'
                        f'Correo: {lead.correo}\n'
                        f'{chr(10).join(message_parts)}\n\n'
                        f'Fecha y hora: {timezone.localtime().strftime("%d/%m/%Y %H:%M %Z")}\n'
                        f'ID de solicitud: {lead.pk}'
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[destinatario],
                    fail_silently=False,
                ) == 1
            except (SMTPException, OSError, ValueError):
                logger.exception(
                    'La solicitud del chatbot %s se guardó, pero falló el correo comercial.',
                    lead.pk,
                )

            if not notification_sent:
                logger.error(
                    'El backend de correo no confirmó la notificación de la solicitud del chatbot %s.',
                    lead.pk,
                )

    return JsonResponse({
        'success': True,
        'message': (
            '¡Gracias por contactar a REMSA Plásticos! Hemos recibido tus datos. '
            'Un asesor comercial dará seguimiento a tu solicitud.'
        ),
    })


def solicitar_catalogo(request):
    if request.method != 'POST':
        return JsonResponse(
            {'success': False, 'message': 'Método no permitido.'},
            status=405,
        )

    if excede_limite_envios(request, 'solicitud_catalogo'):
        return JsonResponse(
            {
                'success': False,
                'message': 'Has enviado demasiadas solicitudes. Intenta de nuevo más tarde.',
            },
            status=429,
        )

    form = SolicitudCatalogoForm(request.POST)
    if not form.is_valid():
        return JsonResponse(
            {
                'success': False,
                'message': 'Revisa los campos marcados e inténtalo de nuevo.',
                'errors': form.errors.get_json_data(),
            },
            status=400,
        )

    site_key = getattr(settings, 'RECAPTCHA_SITE_KEY', '')
    secret_key = getattr(settings, 'RECAPTCHA_SECRET_KEY', '')
    if bool(site_key) != bool(secret_key):
        logger.error('La configuración de reCAPTCHA está incompleta para solicitudes de catálogo.')
        return JsonResponse(
            {
                'success': False,
                'message': 'No se pudo validar el formulario. Intenta más tarde.',
            },
            status=503,
        )

    try:
        captcha_valid = verificar_recaptcha(
            request.POST.get('g-recaptcha-response', ''),
            request,
        )
    except CaptchaConfigurationError:
        logger.exception('La configuración CAPTCHA impidió procesar una solicitud de catálogo.')
        return JsonResponse(
            {
                'success': False,
                'message': 'No se pudo validar el formulario. Intenta más tarde.',
            },
            status=503,
        )
    if not captcha_valid:
        return JsonResponse(
            {
                'success': False,
                'message': 'Completa la validación de seguridad e inténtalo de nuevo.',
                'errors': {'captcha': [{'message': 'Completa la validación de seguridad.'}]},
            },
            status=400,
        )

    values = form.cleaned_data
    try:
        config = ConfiguracionSitio.get_solo()
    except (OperationalError, ProgrammingError):
        logger.exception('No se pudo cargar el correo comercial para solicitud de catálogo.')
        return JsonResponse(
            {
                'success': False,
                'message': 'No pudimos procesar tu solicitud en este momento. Intenta más tarde.',
            },
            status=503,
        )

    recipient = config.correo_notificaciones or settings.COMERCIAL_EMAIL
    if not recipient:
        logger.error('No hay destinatario configurado para solicitudes de catálogo.')
        return JsonResponse(
            {
                'success': False,
                'message': 'No pudimos procesar tu solicitud en este momento. Intenta más tarde.',
            },
            status=503,
        )

    origin_page = values['pagina']
    message = (
        f"Producto de interés: {values['producto']}\n"
        f"Mensaje: {values['mensaje'] or 'Sin mensaje adicional.'}\n\n"
        'Origen: Catálogo web REMSA'
    )
    email_body = (
        'Nueva solicitud de catálogo - REMSA\n\n'
        f"Nombre: {values['nombre']}\n"
        f"Empresa: {values['empresa']}\n"
        f"Correo: {values['correo']}\n"
        f"Teléfono: {values['telefono']}\n\n"
        f"Producto de interés: {values['producto']}\n"
        f"Mensaje: {values['mensaje'] or 'Sin mensaje adicional.'}\n\n"
        f"Fecha y hora: {timezone.localtime().strftime('%d/%m/%Y %H:%M %Z')}\n"
        f"Página: {origin_page}\n"
        'Origen: Catálogo web REMSA\n'
    )

    try:
        sent_count = send_mail(
            subject='Nueva solicitud de catálogo - REMSA',
            message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
    except (SMTPException, OSError, ValueError):
        logger.exception('Falló el envío de una solicitud de catálogo de %s.', values['correo'])
        return JsonResponse(
            {
                'success': False,
                'message': 'No se pudo enviar la solicitud. Intenta de nuevo más tarde.',
            },
            status=503,
        )

    if sent_count != 1:
        logger.error('El backend de correo no confirmó el envío de una solicitud de catálogo.')
        return JsonResponse(
            {
                'success': False,
                'message': 'No se pudo enviar la solicitud. Intenta de nuevo más tarde.',
            },
            status=503,
        )

    MensajeContacto.objects.create(
        nombre=values['nombre'],
        empresa=values['empresa'],
        correo=values['correo'],
        telefono=values['telefono'],
        asunto='Solicitud de catálogo',
        mensaje=message,
        ip_origen=obtener_ip_cliente(request),
    )

    return JsonResponse({'success': True})