import json

from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .chatbot import (
    CONTACT_REPLY,
    GREETING_REPLY,
    INFORMATION_REPLY,
    PRODUCT_REPLY,
    QUOTE_REPLY,
    UNKNOWN_REPLY,
)
from .models import ConfiguracionSitio


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ChatbotTests(TestCase):
    def setUp(self):
        cache.clear()
        ConfiguracionSitio.objects.create(
            correo_notificaciones='notificaciones@remsa.example',
            whatsapp_numero='5219991234567',
        )
        self.endpoint = reverse('chatbot_response')

    def send_message(self, message):
        response = self.client.post(
            self.endpoint,
            data=json.dumps({'message': message}),
            content_type='application/json',
        )
        return response, response.json()

    def test_greetings_ignore_case_accents_and_punctuation(self):
        for greeting in (
            'hola',
            'HOLA!',
            'Buenos días',
            'BUENAS TARDES',
            'buenas noches.',
            '¿Qué tal?',
            'Saludos',
        ):
            with self.subTest(greeting=greeting):
                response, payload = self.send_message(greeting)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(payload['reply'], GREETING_REPLY)
                self.assertFalse(payload['show_form'])

    def test_information_request_shows_contact_form(self):
        for message in (
            'Quiero información',
            'Necesito informes',
            'Quisiera conocer sus productos',
        ):
            with self.subTest(message=message):
                _response, payload = self.send_message(message)
                self.assertEqual(payload['reply'], INFORMATION_REPLY)
                self.assertTrue(payload['show_form'])

    def test_quote_keywords_show_contact_form(self):
        for message in (
            'Quiero cotizar',
            'Cotización',
            '¿Cuánto cuesta?',
            'Solicitar presupuesto',
        ):
            with self.subTest(message=message):
                _response, payload = self.send_message(message)
                self.assertEqual(payload['reply'], QUOTE_REPLY)
                self.assertTrue(payload['show_form'])

    def test_contact_request_shows_contact_form(self):
        for message in ('asesor', 'Quiero hablar con alguien', 'ejecutivo comercial'):
            with self.subTest(message=message):
                _response, payload = self.send_message(message)
                self.assertEqual(payload['reply'], CONTACT_REPLY)
                self.assertTrue(payload['show_form'])

    def test_product_request_includes_real_catalogue_url_and_form(self):
        response, payload = self.send_message('Quiero ver botellas y garrafones')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload['reply'], PRODUCT_REPLY)
        self.assertEqual(payload['catalogue_url'], reverse('catalogo:lista'))
        self.assertTrue(payload['show_form'])

    def test_unknown_request_offers_contact_form_without_echoing_input(self):
        response, payload = self.send_message('<script>alert(1)</script>')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload['reply'], UNKNOWN_REPLY)
        self.assertNotIn('<script>', payload['reply'])
        self.assertTrue(payload['show_form'])

    def test_quick_reply_intent_prefers_quotation_to_product(self):
        _response, payload = self.send_message('Quiero una cotización de botellas')

        self.assertEqual(payload['reply'], QUOTE_REPLY)
        self.assertTrue(payload['show_form'])

    def test_message_is_required_and_length_is_limited(self):
        empty_response, _ = self.send_message('  ')
        long_response, _ = self.send_message('x' * 501)

        self.assertEqual(empty_response.status_code, 400)
        self.assertEqual(long_response.status_code, 413)

    def test_chatbot_widget_contains_welcome_quick_replies_and_lead_form(self):
        response = self.client.get(reverse('contacto:contacto'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '¡Hola! 👋 Bienvenido a REMSA Plásticos. ¿En qué podemos ayudarte?',
        )
        for label in (
            'Quiero información',
            'Quiero una cotización',
            'Ver productos',
            'Hablar con un asesor',
            'Solicitar contacto',
        ):
            self.assertContains(response, label)
        for field in ('nombre', 'empresa', 'telefono', 'correo', 'producto', 'mensaje'):
            self.assertContains(response, f'name="{field}"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertContains(response, 'data-lead-endpoint="/contacto/chatbot/solicitar-contacto/"')
        self.assertContains(response, 'id="chatbotPanel"')

    def test_chatbot_endpoint_requires_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(
            self.endpoint,
            data=json.dumps({'message': 'hola'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 403)

    def test_whatsapp_float_is_hidden_by_default(self):
        response = self.client.get(reverse('contacto:contacto'))

        self.assertNotContains(response, 'class="whatsapp-float"')

    @override_settings(SHOW_WHATSAPP_FLOAT=True)
    def test_whatsapp_float_can_be_enabled_without_changing_its_widget(self):
        response = self.client.get(reverse('contacto:contacto'))

        self.assertContains(response, 'class="whatsapp-float"')
