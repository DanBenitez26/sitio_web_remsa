from html.parser import HTMLParser
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from apps.catalogo.models import Categoria, Producto
from apps.core.models import ConfiguracionSitio
from .models import SolicitudCotizacion


class FormNestingParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.form_depth = 0
        self.has_nested_forms = False

    def handle_starttag(self, tag, attrs):
        if tag == 'form':
            self.has_nested_forms |= self.form_depth > 0
            self.form_depth += 1

    def handle_endtag(self, tag):
        if tag == 'form' and self.form_depth:
            self.form_depth -= 1


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='sitio@remsa.example',
    COMERCIAL_EMAIL='ventas@remsa.example',
)
class CotizacionTests(TestCase):
    def setUp(self):
        categoria = Categoria.objects.create(nombre="Botellas")
        self.producto = Producto.objects.create(
            nombre="Botella PET 600ml", categoria=categoria, material="PET", activo=True,
        )
        ConfiguracionSitio.objects.create(correo_notificaciones='notificaciones@remsa.example')

    def test_agregar_al_carrito(self):
        response = self.client.post(
            reverse('cotizaciones:agregar', args=[self.producto.pk]),
            {'cantidad': 2}
        )
        self.assertEqual(response.status_code, 302)
        session = self.client.session
        self.assertEqual(session['carrito'][str(self.producto.pk)], 2)

    def test_enviar_solicitud_crea_folio(self):
        self.client.post(reverse('cotizaciones:agregar', args=[self.producto.pk]), {'cantidad': 1})
        response = self.client.post(reverse('cotizaciones:carrito'), {
            'nombre': 'Cliente de prueba',
            'correo': 'cliente@example.com',
            'mensaje': 'Prueba',
            'sitio_web': '',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(SolicitudCotizacion.objects.count(), 1)
        solicitud = SolicitudCotizacion.objects.first()
        self.assertTrue(solicitud.folio.startswith('REMSA-'))
        self.assertEqual(solicitud.items.count(), 1)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].to, ['notificaciones@remsa.example'])
        self.assertEqual(mail.outbox[1].to, ['cliente@example.com'])
        self.assertIn(solicitud.folio, mail.outbox[0].subject)
        self.assertIn(solicitud.folio, mail.outbox[1].subject)

    def test_pagina_del_carrito_no_contiene_formularios_anidados(self):
        self.client.post(reverse('cotizaciones:agregar', args=[self.producto.pk]), {'cantidad': 1})
        response = self.client.get(reverse('cotizaciones:carrito'))
        parser = FormNestingParser()
        parser.feed(response.content.decode())
        self.assertFalse(parser.has_nested_forms)

    def test_intenta_confirmar_al_cliente_aunque_falle_correo_comercial(self):
        self.client.post(reverse('cotizaciones:agregar', args=[self.producto.pk]), {'cantidad': 1})
        with patch(
            'apps.cotizaciones.services.send_mail',
            side_effect=[RuntimeError('SMTP de prueba'), 1],
        ) as send:
            response = self.client.post(reverse('cotizaciones:carrito'), {
                'nombre': 'Cliente de prueba',
                'correo': 'cliente@example.com',
                'mensaje': 'Prueba',
                'sitio_web': '',
            })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(send.call_count, 2)
        self.assertEqual(SolicitudCotizacion.objects.count(), 1)

    def test_honeypot_bloquea_envio(self):
        self.client.post(reverse('cotizaciones:agregar', args=[self.producto.pk]), {'cantidad': 1})
        response = self.client.post(reverse('cotizaciones:carrito'), {
            'nombre': 'Bot',
            'correo': 'bot@example.com',
            'mensaje': 'spam',
            'sitio_web': 'http://spam.com',
        })
        self.assertEqual(SolicitudCotizacion.objects.count(), 0)
