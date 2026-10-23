from tempfile import TemporaryDirectory
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse
from openpyxl import Workbook

from .catalogue import PUBLIC_CATALOG_CATEGORIES
from .management.commands.importar_catalogo_excel import HEADERS
from .models import Categoria, EspecificacionProducto, Producto, Servicio


class CatalogoTests(TestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(nombre="Botellas")
        self.producto = Producto.objects.create(
            nombre="Botella PET 600ml", categoria=self.categoria,
            material="PET", tipo="BOTELLA", activo=True,
        )
        self.producto_inactivo = Producto.objects.create(
            nombre="Producto descontinuado", categoria=self.categoria,
            material="PET", activo=False,
        )

    def test_servicio_proteccion_uv_abre_modal_con_envases_ilustrativos(self):
        Servicio.objects.create(
            nombre="Protección UV",
            descripcion_corta="Aditivo de protección UV.",
            activo=True,
        )

        response = self.client.get(reverse("catalogo:servicios"))

        self.assertContains(response, 'data-bs-target="#proteccionUvModal"')
        self.assertContains(response, 'id="proteccionUvModal"')
        self.assertContains(response, "Los aditivos con protección UV")
        self.assertContains(response, "Botellas PET")
        self.assertContains(response, "Garrafas PET")
        self.assertContains(response, "Garrafas PEAD")
        self.assertContains(response, "Las imágenes son ilustrativas.")

    def test_detalle_de_pigmentado_muestra_galeria_de_colores(self):
        servicio = Servicio.objects.create(
            nombre="Pigmentado de envases",
            descripcion_corta="Pigmentado según la paleta de la marca.",
            activo=True,
        )

        response = self.client.get(servicio.get_absolute_url())

        self.assertContains(response, "pigmentado-gallery")
        self.assertContains(response, "img_envases_varios.png")
        self.assertContains(response, "img-tapas.png")
        self.assertContains(response, "Tapas para completar tu presentación")
        self.assertContains(response, "botellas PET y PEAD")
        for color in ("Azul genérico", "Azul cobalto", "Morado", "Verde acqua", "Rosa", "Transparente"):
            with self.subTest(color=color):
                self.assertContains(response, color)

    def test_detalle_de_personalizacion_incluye_botellas_y_tapas(self):
        servicio = Servicio.objects.create(
            nombre="Personalización de garrafones",
            descripcion_corta="Personaliza tu envase.",
            activo=True,
        )

        response = self.client.get(servicio.get_absolute_url())

        self.assertContains(response, "Botellas")
        self.assertContains(response, "Tapas de PP")
        self.assertContains(response, "img-tapas.png")

    def test_tarjetas_de_servicios_usan_iconos_relacionados_con_su_titulo(self):
        for nombre in (
            "Personalización de garrafones",
            "Pigmentado de envases",
            "Protección UV",
        ):
            Servicio.objects.create(nombre=nombre, activo=True)

        for url in (reverse("catalogo:servicios"),):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, "bi-box-seam")
                self.assertContains(response, "bi-palette-fill")
                self.assertContains(response, "bi-sun-fill")

    def test_home_oculta_bloque_de_soluciones_y_destaca_logistica_y_proceso(self):
        Servicio.objects.create(nombre="Pigmentado de envases", activo=True)

        response = self.client.get(reverse("paginas:home"))

        self.assertNotContains(response, "Soluciones configurables para tu producto")
        self.assertNotContains(response, "Pigmentado de envases")
        self.assertContains(response, "Cómo trabajamos")
        self.assertContains(response, "Proceso de fabricación y atención comercial")
        self.assertContains(response, "img_logistica_carga.png")

    def test_pagina_de_soluciones_muestra_portada_e_imagenes_de_apoyo(self):
        Servicio.objects.create(
            nombre="Pigmentado de envases",
            descripcion_corta="Pigmentado según la paleta de la marca.",
            activo=True,
        )

        response = self.client.get(reverse("catalogo:servicios"))

        self.assertContains(response, "Soluciones REMSA")
        self.assertContains(response, "soluciones-disponibles")
        self.assertContains(response, "img_calidad.png")
        self.assertContains(response, "laboratorio_remsa.png")
        self.assertContains(response, "Garrafones de distintos colores")
        self.assertContains(response, "img_botella.png")
        self.assertContains(response, "img_envases_varios.png")
        self.assertContains(response, "img_pead.png")
        self.assertContains(response, "Colores de referencia")
        self.assertContains(response, ">Soluciones</a>")

    def test_lista_productos_solo_muestra_activos(self):
        response = self.client.get(reverse('catalogo:lista'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Productos principales")
        self.assertContains(response, "Botellas PET")
        self.assertNotContains(response, "Botella PET 600ml")
        self.assertEqual(response.context['productos'], [])
        self.assertNotContains(response, "Producto descontinuado")

    def test_listado_de_categoria_pagina_en_bloques_de_12(self):
        for index in range(14):
            Producto.objects.create(
                nombre=f'Botella adicional {index}',
                categoria=self.categoria,
                tipo='BOTELLA',
                activo=True,
            )

        response = self.client.get(reverse('catalogo:lista'), {'categoria': 'botellas'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['productos']), 12)
        self.assertEqual(response.context['page_obj'].paginator.count, 15)
        self.assertContains(response, 'Página 1 de 2')
        self.assertEqual(response.content.count(b'data-catalog-request'), 12)

    def test_lista_muestra_solo_los_campos_publicados_del_catalogo(self):
        self.producto.descripcion_corta = "Envase para bebidas."
        self.producto.capacidad = "600 ml"
        self.producto.color = "Transparente"
        self.producto.aplicaciones = "Este texto no debe mostrarse."
        self.producto.save()

        response = self.client.get(
            reverse('catalogo:lista'),
            {'categoria': 'botellas'},
        )

        self.assertContains(response, "Envase para bebidas.")
        self.assertContains(response, "<dt>Capacidad / medida</dt><dd>600 ml</dd>")
        self.assertContains(response, "<dt>Color</dt><dd>Transparente</dd>")
        self.assertNotContains(response, "Este texto no debe mostrarse.")
        self.assertNotContains(response, "Aplicaciones")
        self.assertNotContains(response, 'class="catalogo-datos"')
        self.assertContains(response, '?categoria=botellas')

    def test_detalles_por_producto_muestran_descripcion_y_especificaciones_separadas(self):
        self.producto.descripcion = 'Diseñada para envasar salsas.'
        self.producto.material = 'PET'
        self.producto.save()
        EspecificacionProducto.objects.create(
            producto=self.producto,
            nombre='Peso',
            valor='19 g',
        )
        EspecificacionProducto.objects.create(
            producto=self.producto,
            nombre='Altura',
            valor='169.5 mm',
        )

        response = self.client.get(
            reverse('catalogo:lista'),
            {'categoria': 'botellas'},
        )

        self.assertContains(response, 'data-product-detail="detalleProducto-')
        self.assertContains(response, 'Diseñada para envasar salsas.')
        self.assertContains(response, '<dt>Peso</dt><dd>19 g</dd>')
        self.assertContains(response, '<dt>Altura</dt><dd>169.5 mm</dd>')

    def test_lista_oculta_productos_fuera_del_catalogo_publico(self):
        self.producto.en_catalogo = False
        self.producto.save(update_fields=['en_catalogo'])

        response = self.client.get(reverse('catalogo:lista'))

        self.assertNotContains(response, self.producto.nombre)

    @override_settings(
        RECAPTCHA_SITE_KEY='public-site-key',
        RECAPTCHA_SECRET_KEY='private-secret-key',
    )
    def test_catalogo_expone_solo_la_clave_publica_de_recaptcha(self):
        response = self.client.get(reverse('catalogo:lista'))

        self.assertContains(response, 'public-site-key')
        self.assertContains(response, 'data-recaptcha-enabled="true"')
        self.assertNotContains(response, 'private-secret-key')

    def test_catalogo_solo_incluye_categorias_solicitadas(self):
        categoria_no_publica = Categoria.objects.create(nombre='Material reciclado')
        Producto.objects.create(
            nombre='Molido PEAD Azul',
            categoria=categoria_no_publica,
            tipo='Material reciclado',
            activo=True,
            en_catalogo=True,
        )

        response = self.client.get(reverse('catalogo:lista'))
        category_slugs = [category[0] for category in response.context['categorias']]
        category_labels = [category[1] for category in response.context['categorias']]

        product_response = self.client.get(
            reverse('catalogo:lista'),
            {'categoria': 'botellas'},
        )
        self.assertContains(product_response, self.producto.nombre)
        self.assertNotContains(response, 'Molido PEAD Azul')
        self.assertEqual(category_labels, list(PUBLIC_CATALOG_CATEGORIES))
        self.assertNotIn('material-reciclado', category_slugs)
        self.assertIn('Frascos', category_labels)
        self.assertEqual(
            self.client.get(reverse('catalogo:lista'), {'categoria': 'frascos'})
            .context['productos'],
            [],
        )
        type_values = [value for value, _label in response.context['tipos']]
        self.assertNotIn('Resina', type_values)
        self.assertEqual(len(PUBLIC_CATALOG_CATEGORIES), 7)

    def test_lineas_principales_muestran_imagenes_de_referencia_en_lugar_de_iconos(self):
        response = self.client.get(reverse('catalogo:lista'))

        for image_path in (
            'img/img-remsa/Garrafones y botellones.png',
            'img/img-remsa/Botella Pet.png',
            'img/img-remsa/img_asas.jpg',
            'img/img-remsa/img-home-productos/img-tapas.png',
            'img/img-remsa/img-home-productos/img_preformas_pet.png',
            'img/img-remsa/frasco Pet.png',
            'img/img-remsa/Garrafas Pet.png',
            'img/img-remsa/Garrafas Pead.png',
        ):
            with self.subTest(image_path=image_path):
                self.assertContains(response, image_path.replace(' ', '%20'))

        self.assertNotContains(response, 'catalogo-categoria-icon')

    def test_filtro_por_categoria(self):
        otra_categoria = Categoria.objects.create(nombre="Garrafones")
        Producto.objects.create(nombre="Garrafon 19L", categoria=otra_categoria, activo=True)
        response = self.client.get(reverse('catalogo:lista'), {'categoria': self.categoria.slug})
        self.assertContains(response, "Botella PET 600ml")
        self.assertNotContains(response, "Garrafon 19L")

    def test_busqueda_y_filtros_usan_datos_del_producto(self):
        self.producto.tipo = 'Botella PET'
        self.producto.color = 'Transparente'
        self.producto.capacidad = '600 ml'
        self.producto.save()
        EspecificacionProducto.objects.create(
            producto=self.producto,
            nombre='Material',
            valor='PET cristal',
        )

        by_specification = self.client.get(
            reverse('catalogo:lista'),
            {'q': 'cristal'},
        )
        by_type = self.client.get(
            reverse('catalogo:lista'),
            {'tipo': 'Botella PET'},
        )
        by_color_and_measure = self.client.get(
            reverse('catalogo:lista'),
            {'color': 'Transparente', 'medida': '600 ml'},
        )

        self.assertContains(by_specification, self.producto.nombre)
        self.assertContains(by_type, self.producto.nombre)
        self.assertContains(by_color_and_measure, self.producto.nombre)

    def test_filtro_tipo_muestra_una_opcion_por_tipo(self):
        Producto.objects.create(
            nombre='Otra botella PET',
            categoria=self.categoria,
            tipo='BOTELLA',
            activo=True,
        )
        Producto.objects.create(
            nombre='Una botella PET más',
            categoria=self.categoria,
            tipo='BOTELLA',
            activo=True,
        )

        response = self.client.get(
            reverse('catalogo:lista'),
            {'categoria': 'botellas'},
        )
        type_options = [value for value, _label in response.context['tipos']]

        self.assertEqual(len(type_options), len(set(type_options)))
        self.assertEqual(response.content.count(b'<option value="BOTELLA"'), 1)

    def test_detalle_producto(self):
        response = self.client.get(self.producto.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Botella PET 600ml")

    def test_detalle_producto_inactivo_da_404(self):
        response = self.client.get(self.producto_inactivo.get_absolute_url())
        self.assertEqual(response.status_code, 404)

    def test_producto_legacy_conserva_el_detalle_para_enlaces_existentes(self):
        self.producto.en_catalogo = False
        self.producto.save(update_fields=['en_catalogo'])

        response = self.client.get(self.producto.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.producto.nombre)

    def test_descarga_ficha_pdf(self):
        self.producto.descripcion_corta = "Envase para bebidas."
        self.producto.capacidad = "600 ml"
        self.producto.color = "Transparente"
        self.producto.save()

        response = self.client.get(reverse(
            'catalogo:ficha_pdf',
            kwargs={'slug': self.producto.slug},
        ))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('.pdf', response['Content-Disposition'])
        pdf_content = b''.join(response.streaming_content)
        self.assertTrue(pdf_content.startswith(b'%PDF-'))
        self.assertLess(len(pdf_content), 1_000_000)

    def test_importa_excel_sin_duplicar_y_preserva_datos_exactos(self):
        with TemporaryDirectory() as directory:
            workbook_path = Path(directory) / 'catalogo.xlsx'
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = 'Catalogo'
            sheet.append(HEADERS)
            sheet.append([
                'Preformas',
                'Preforma 13g CSN 26mm Cristal',
                'Preforma de PET para proceso de soplado.',
                '26 mm',
                'Cristal',
                'Preforma',
                'Peso: 13 g; Boca: 26 mm; Estándar/modelo: CSN',
                'Fabricación de botellas y envases mediante proceso de soplado.',
                'Modelo 1000-21',
            ])
            sheet.append([None] * len(HEADERS))
            workbook.save(workbook_path)

            call_command('importar_catalogo_excel', workbook_path)
            product = Producto.objects.get(nombre='Preforma 13g CSN 26mm Cristal')
            product.descripcion = 'Descripción de producto capturada en Admin.'
            product.save(update_fields=['descripcion'])
            EspecificacionProducto.objects.create(
                producto=product,
                nombre='Peso',
                valor='13 g',
            )
            call_command('importar_catalogo_excel', workbook_path)

        product = Producto.objects.get(nombre='Preforma 13g CSN 26mm Cristal')
        self.assertEqual(product.tipo, 'Preforma')
        self.assertEqual(product.material, '')
        self.assertEqual(product.capacidad, '26 mm')
        self.assertEqual(product.color, 'Cristal')
        self.assertEqual(product.descripcion_corta, 'Preforma de PET para proceso de soplado.')
        self.assertTrue(product.en_catalogo)
        self.assertEqual(product.descripcion, 'Descripción de producto capturada en Admin.')
        self.assertEqual(product.especificaciones.count(), 3)
        self.assertEqual(
            product.especificaciones.get(nombre='Peso').valor,
            '13 g',
        )
        self.assertEqual(
            product.especificaciones.get(
                nombre='Especificaciones técnicas',
            ).valor,
            'Peso: 13 g; Boca: 26 mm; Estándar/modelo: CSN',
        )
        self.assertEqual(
            product.especificaciones.get(nombre='Variante').valor,
            'Modelo 1000-21',
        )
        response = self.client.get(
            reverse('catalogo:lista'),
            {'categoria': 'preformas'},
        )
        card_markup = response.content.decode().split(
            '<template id="detalleProducto-',
            maxsplit=1,
        )[0]
        self.assertNotIn('Peso: 13 g; Boca: 26 mm; Estándar/modelo: CSN', card_markup)
        self.assertContains(response, 'Peso: 13 g; Boca: 26 mm; Estándar/modelo: CSN')
        self.assertNotContains(
            response,
            'Especificaciones técnicas: Peso: 13 g; Boca: 26 mm',
        )
        self.assertEqual(
            Producto.objects.filter(nombre='Preforma 13g CSN 26mm Cristal').count(),
            1,
        )
        self.assertFalse(Producto.objects.get(pk=self.producto.pk).en_catalogo)

    def test_importador_rechaza_nombres_duplicados(self):
        with TemporaryDirectory() as directory:
            workbook_path = Path(directory) / 'catalogo.xlsx'
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = 'Catalogo'
            sheet.append(HEADERS)
            record = [
                'Preformas', 'Preforma repetida', 'Descripción', '', '', 'Preforma',
                '', '', '',
            ]
            sheet.append(record)
            sheet.append(record)
            workbook.save(workbook_path)

            with self.assertRaises(CommandError):
                call_command('importar_catalogo_excel', workbook_path)

        self.assertFalse(Producto.objects.filter(nombre='Preforma repetida').exists())

    def test_slug_autogenerado(self):
        self.assertEqual(self.producto.slug, "botella-pet-600ml")
