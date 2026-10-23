from django.core import mail
from django.core.cache import cache
from django.db import OperationalError
from django.test import TestCase, override_settings
from django.urls import reverse
from smtplib import SMTPException
from unittest.mock import patch
from uuid import uuid4

from apps.core.models import ConfiguracionSitio
from .models import MensajeContacto


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='sitio@remsa.example',
    COMERCIAL_EMAIL='ventas@remsa.example',
    RECAPTCHA_SITE_KEY='',
    RECAPTCHA_SECRET_KEY='',
)
class SolicitudCatalogoTests(TestCase):
    def setUp(self):
        cache.clear()
        ConfiguracionSitio.objects.create(
            correo_notificaciones='notificaciones@remsa.example',
        )
        self.url = reverse('contacto:solicitar_catalogo')
        self.data = {
            'nombre': 'Ana Pérez',
            'empresa': 'Acme',
            'correo': 'ana@acme.example',
            'telefono': '+52 999 123 4567',
            'producto': 'Botella PET 500 ml',
            'mensaje': 'Buscamos opciones para bebidas.',
            'pagina': '/catalogo/?categoria=botellas',
            'acepta_privacidad': 'true',
            'sitio_web': '',
        }

    def post_request(self, values=None):
        return self.client.post(self.url, values or self.data)

    def test_envia_correo_y_guarda_la_solicitud_con_producto_de_interes(self):
        response = self.post_request()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True})
        self.assertEqual(len(mail.outbox), 1)
        notification = mail.outbox[0]
        self.assertEqual(notification.subject, 'Nueva solicitud de catálogo - REMSA')
        self.assertEqual(notification.to, ['notificaciones@remsa.example'])
        for expected in (
            'Nombre: Ana Pérez',
            'Empresa: Acme',
            'Correo: ana@acme.example',
            'Teléfono: +52 999 123 4567',
            'Producto de interés: Botella PET 500 ml',
            'Mensaje: Buscamos opciones para bebidas.',
            'Página: /catalogo/?categoria=botellas',
            'Origen: Catálogo web REMSA',
            'Fecha y hora:',
        ):
            self.assertIn(expected, notification.body)

        saved = MensajeContacto.objects.get()
        self.assertEqual(saved.asunto, 'Solicitud de catálogo')
        self.assertEqual(saved.empresa, 'Acme')
        self.assertIn('Botella PET 500 ml', saved.mensaje)

    def test_privacidad_es_obligatoria(self):
        data = {**self.data}
        data.pop('acepta_privacidad')

        response = self.post_request(data)

        self.assertEqual(response.status_code, 400)
        self.assertIn('acepta_privacidad', response.json()['errors'])
        self.assertEqual(len(mail.outbox), 0)

    def test_correo_telefono_y_producto_se_validan_en_el_backend(self):
        invalid_data = [
            ({**self.data, 'correo': 'no-es-correo'}, 'correo'),
            ({**self.data, 'telefono': '123'}, 'telefono'),
            ({**self.data, 'producto': ''}, 'producto'),
        ]
        for data, field in invalid_data:
            with self.subTest(field=field):
                response = self.post_request(data)
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.json()['errors'])
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(RECAPTCHA_SITE_KEY='public-key', RECAPTCHA_SECRET_KEY='secret-key')
    def test_falta_de_respuesta_de_captcha_impide_el_envio(self):
        from unittest.mock import patch

        with patch('apps.contacto.views.verificar_recaptcha', return_value=False):
            response = self.post_request()

        self.assertEqual(response.status_code, 400)
        self.assertIn('captcha', response.json()['errors'])
        self.assertEqual(len(mail.outbox), 0)

    def test_honeypot_impide_el_envio(self):
        response = self.post_request({**self.data, 'sitio_web': 'spam'})

        self.assertEqual(response.status_code, 400)
        self.assertIn('sitio_web', response.json()['errors'])
        self.assertEqual(len(mail.outbox), 0)

    def test_endpoint_solo_acepta_post(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='sitio@remsa.example',
    COMERCIAL_EMAIL='ventas@remsa.example',
)
class ChatbotLeadTests(TestCase):
    def setUp(self):
        cache.clear()
        ConfiguracionSitio.objects.create(
            correo_notificaciones='notificaciones@remsa.example',
        )
        self.url = reverse('contacto:chatbot_lead')
        self.data = {
            'nombre': ' Ana Pérez ',
            'empresa': ' Acme Industrial ',
            'telefono': '+52 999 123 4567',
            'correo': 'ana@acme.example',
            'producto': 'Envase PET',
            'mensaje': ' Solicito información de cotización. ',
            'sitio_web': '',
            'submission_id': str(uuid4()),
        }

    def test_valid_lead_is_saved_and_notifies_commercial_recipient(self):
        response = self.client.post(self.url, self.data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(
            response.json()['message'],
            '¡Gracias por contactar a REMSA Plásticos! Hemos recibido tus datos. '
            'Un asesor comercial dará seguimiento a tu solicitud.',
        )
        lead = MensajeContacto.objects.get()
        self.assertEqual(lead.nombre, 'Ana Pérez')
        self.assertEqual(lead.empresa, 'Acme Industrial')
        self.assertEqual(lead.correo, 'ana@acme.example')
        self.assertIn('Producto de interés: Envase PET', lead.mensaje)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['notificaciones@remsa.example'])
        self.assertIn('Ana Pérez', mail.outbox[0].body)

    def test_invalid_required_fields_are_rejected_without_saving(self):
        invalid_requests = (
            ({**self.data, 'correo': 'correo-inválido'}, 'correo'),
            ({**self.data, 'telefono': '12345'}, 'telefono'),
            ({**self.data, 'empresa': ''}, 'empresa'),
            ({**self.data, 'nombre': ''}, 'nombre'),
        )
        for values, field in invalid_requests:
            with self.subTest(field=field):
                response = self.client.post(self.url, values)
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.json()['errors'])
        self.assertEqual(MensajeContacto.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_missing_submission_id_is_rejected(self):
        values = {key: value for key, value in self.data.items() if key != 'submission_id'}

        response = self.client.post(self.url, values)

        self.assertEqual(response.status_code, 400)
        self.assertIn('submission_id', response.json()['errors'])
        self.assertEqual(MensajeContacto.objects.count(), 0)

    def test_honeypot_rejects_spam(self):
        response = self.client.post(self.url, {**self.data, 'sitio_web': 'spam'})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(MensajeContacto.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_repeated_submission_id_does_not_create_duplicate_leads(self):
        first = self.client.post(self.url, self.data)
        second = self.client.post(self.url, self.data)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(MensajeContacto.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_database_record_is_confirmed_even_if_email_notification_fails(self):
        with patch(
            'apps.contacto.views.send_mail',
            side_effect=SMTPException('SMTP test failure'),
        ):
            response = self.client.post(self.url, self.data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(MensajeContacto.objects.count(), 1)

    def test_database_failure_does_not_report_success(self):
        with patch(
            'apps.contacto.views.MensajeContacto.objects.create',
            side_effect=OperationalError('database unavailable'),
        ):
            response = self.client.post(self.url, self.data)

        self.assertEqual(response.status_code, 500)
        self.assertFalse(response.json()['success'])
        self.assertEqual(MensajeContacto.objects.count(), 0)

    def test_console_email_backend_keeps_lead_and_logs_missing_email_delivery(self):
        with override_settings(
            EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend',
        ):
            with patch('apps.contacto.views.send_mail') as send:
                with self.assertLogs('apps.contacto.views', level='ERROR'):
                    response = self.client.post(self.url, self.data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(MensajeContacto.objects.count(), 1)
        send.assert_not_called()

    def test_chatbot_lead_endpoint_requires_csrf(self):
        from django.test import Client

        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(self.url, self.data)

        self.assertEqual(response.status_code, 403)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='sitio@remsa.example',
    COMERCIAL_EMAIL='ventas@remsa.example',
    RECAPTCHA_SITE_KEY='',
    RECAPTCHA_SECRET_KEY='',
)
class ContactoCentroamericaTests(TestCase):
    def setUp(self):
        cache.clear()
        ConfiguracionSitio.objects.create(correo_notificaciones='notificaciones@remsa.example')
        self.url = reverse('contacto:contacto_centroamerica')
        self.data = {
            'nombre': 'Ana Pérez',
            'empresa': 'Acme',
            'correo': 'ana@acme.example',
            'telefono': '+502 5555 1234',
            'asunto': 'Cotización de envases',
            'mensaje': 'Necesitamos información de productos.',
            'acepta_privacidad': 'true',
            'sitio_web': '',
        }

    def test_envia_correo_con_reply_to(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['notificaciones@remsa.example'])
        self.assertEqual(email.from_email, 'sitio@remsa.example')
        self.assertEqual(email.reply_to, ['ana@acme.example'])
        self.assertIn('Recipientes y Empaques de Centroamérica, S.A.', email.body)
        self.assertIn('Fecha y hora de recepción', email.body)

    def test_rechaza_datos_invalidos_y_honeypot(self):
        for cambio in ({'correo': 'x'}, {'telefono': 'abc'}, {'acepta_privacidad': ''}, {'sitio_web': 'bot'}):
            response = self.client.post(self.url, {**self.data, **cambio})
            self.assertEqual(response.status_code, 400)
        self.assertEqual(len(mail.outbox), 0)

    def test_pagina_contacto_muestra_seccion_y_mapa(self):
        response = self.client.get(reverse('contacto:contacto'))
        self.assertContains(response, 'Recipientes y Empaques de Centroamérica, S.A.')
        self.assertContains(response, 'Abrir en Google Maps')

    def test_error_smtp_devuelve_502(self):
        with patch('django.core.mail.EmailMessage.send', side_effect=SMTPException):
            response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 502)
