import json
import logging
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings

from apps.core.utils import obtener_ip_cliente

logger = logging.getLogger(__name__)


class CaptchaConfigurationError(Exception):
    pass


def verificar_recaptcha(token, request):
    site_key = getattr(settings, 'RECAPTCHA_SITE_KEY', '')
    secret_key = getattr(settings, 'RECAPTCHA_SECRET_KEY', '')
    if not site_key and not secret_key:
        return True
    if not site_key or not secret_key:
        raise CaptchaConfigurationError('Falta configurar ambas claves de reCAPTCHA.')
    if not token:
        return False

    payload = {
        'secret': secret_key,
        'response': token,
    }
    client_ip = obtener_ip_cliente(request)
    if client_ip:
        payload['remoteip'] = client_ip

    verification_request = Request(
        'https://www.google.com/recaptcha/api/siteverify',
        data=urlencode(payload).encode('ascii'),
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        method='POST',
    )

    try:
        with urlopen(verification_request, timeout=5) as response:
            result = json.loads(response.read().decode('utf-8'))
    except (URLError, TimeoutError, ValueError):
        logger.exception('No se pudo validar el CAPTCHA de la solicitud de catálogo.')
        return False

    return result.get('success') is True
