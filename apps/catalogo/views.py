from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from django.conf import settings
from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator
from django.utils.text import slugify
from PIL import Image as PillowImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .catalogue import PUBLIC_CATALOG_CATEGORIES
from .models import Producto, Servicio


CATEGORY_DISPLAY = {
    'Garrafones': (
        ('img/img-remsa/envase-garrafon-azul-generico.png',),
        'Garrafones',
    ),
    'Botellas': (
        ('img/img-remsa/img-catalogo/botellas_pet.png',),
        'Botellas PET',
    ),
    'Asas': (('img/img-remsa/img_asa.png',), 'Asas'),
    'Tapas': (
        ('img/img-remsa/img-home-productos/img-tapas.png',),
        'Tapas',
    ),
    'Preformas': (
        ('img/img-remsa/img-home-productos/img_preformas_pet.png',),
        'Preformas',
    ),
    'Frascos': (('img/img-remsa/frasco Pet.png',), 'Frascos PET'),
    'Garrafas PET': (('img/img-remsa/Garrafas Pet.png',), 'Garrafas PET'),
    'Garrafas PEAD': (('img/img-remsa/Garrafas Pead.png',), 'Garrafas PEAD'),
}


CATALOGO_DIGITAL_URL = 'https://xac.lat/'
#'https://online.fliphtml5.com/sczoh/CATALOGO-REMSA/'


CATEGORY_DESCRIPTIONS = {
    'Garrafones': 'Garrafones para agua y otras soluciones de envasado.',
    'Botellas': 'Botellas PET para productos con una presentación confiable.',
    'Asas': 'Asas para envases y garrafas, pensadas para un manejo práctico.',
    'Tapas': 'Tapas y componentes para completar tus soluciones de empaque.',
    'Preformas': 'Preformas de PET para diferentes capacidades y aplicaciones.',
    'Frascos': (
        'El modelo 63 de frasco PET de 250 ml es ideal para quien busca envasar '
        'salsas, mermelada, conservas o cualquier producto que requiera envase '
        'de estas dimensiones.'
    ),
    'Garrafas PET': 'Garrafas de PET para diferentes capacidades y aplicaciones.',
    'Garrafas PEAD': 'Garrafas de PEAD para diferentes capacidades y aplicaciones.',
}


def _annotate_catalogue_products(products):
    for product in products:
        product.catalogo_tipo = product.get_tipo_display()
        product.catalogo_especificaciones = '; '.join(
            spec.valor if spec.nombre == 'Especificaciones técnicas'
            else f'{spec.nombre}: {spec.valor}'
            for spec in product.especificaciones.all()
        )
        product.catalogo_busqueda = ' '.join(filter(None, (
            product.nombre,
            product.descripcion_corta,
            product.tipo,
            product.catalogo_tipo,
            product.capacidad,
            product.color,
            product.catalogo_especificaciones,
        )))
    return products


def lista_productos(request):
    catalogo = Producto.objects.filter(
        activo=True,
        en_catalogo=True,
        categoria__nombre__in=PUBLIC_CATALOG_CATEGORIES,
    ).select_related('categoria').prefetch_related('especificaciones', 'galeria')

    categoria_slug = request.GET.get('categoria', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    color = request.GET.get('color', '').strip()
    medida = request.GET.get('medida', '').strip()
    query = request.GET.get('q', '').strip()

    if categoria_slug:
        category_names = [
            name for name in PUBLIC_CATALOG_CATEGORIES
            if slugify(name) == categoria_slug
        ]
        if category_names:
            catalogo = catalogo.filter(categoria__nombre__in=category_names)
        else:
            catalogo = catalogo.none()

    productos = catalogo
    if tipo:
        productos = productos.filter(tipo=tipo)
    if color:
        productos = productos.filter(color=color)
    if medida:
        productos = productos.filter(capacidad=medida)
    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) |
            Q(descripcion_corta__icontains=query) |
            Q(tipo__icontains=query) |
            Q(capacidad__icontains=query) |
            Q(color__icontains=query) |
            Q(especificaciones__valor__icontains=query)
        ).distinct()

    total_productos = catalogo.count()
    show_products = any((categoria_slug, tipo, color, medida, query))
    paginator = Paginator(productos.order_by('orden', 'nombre'), 12)
    page_obj = paginator.get_page(request.GET.get('page')) if show_products else None
    productos = _annotate_catalogue_products(
        list(page_obj.object_list) if page_obj else []
    )
    type_values = (
        catalogo.order_by()
        .order_by()
        .values_list('tipo', flat=True).distinct()
    )
    type_labels = dict(Producto.TIPO_CHOICES)
    tipos = [
        (value, type_labels.get(value, value))
        for value in sorted(type_values, key=str.casefold)
        if value
    ]
    categorias = [
        (
            slugify(category),
            category,
            *CATEGORY_DISPLAY[category],
            Producto.objects.filter(
                activo=True,
                en_catalogo=True,
                categoria__nombre=category,
            ).count(),
            CATEGORY_DESCRIPTIONS.get(category, ''),
        )
        for category in PUBLIC_CATALOG_CATEGORIES
    ]
    colores = sorted(
        set(catalogo
            .exclude(color='').values_list('color', flat=True)),
        key=str.casefold,
    )
    medidas = sorted(
        set(catalogo
            .exclude(capacidad='').values_list('capacidad', flat=True)),
        key=str.casefold,
    )

    contexto = {
        'productos': productos,
        'page_obj': page_obj,
        'total_productos': total_productos,
        'show_products': show_products,
        'categorias': categorias,
        'categoria_actual': categoria_slug,
        'catalogo_digital_url': CATALOGO_DIGITAL_URL,
        # Poner en True para reactivar «Solicitar catálogo» y «Ficha PDF».
        'mostrar_solicitud_catalogo': False,
        'mostrar_ficha_pdf': False,
        'tipos': tipos,
        'colores': colores,
        'medidas': medidas,
        'tipo_actual': tipo,
        'color_actual': color,
        'medida_actual': medida,
        'query': query,
        'recaptcha_site_key': getattr(settings, 'RECAPTCHA_SITE_KEY', ''),
        'recaptcha_enabled': bool(
            getattr(settings, 'RECAPTCHA_SITE_KEY', '')
            and getattr(settings, 'RECAPTCHA_SECRET_KEY', '')
        ),
        'recaptcha_config_incomplete': bool(
            getattr(settings, 'RECAPTCHA_SITE_KEY', '')
        ) != bool(getattr(settings, 'RECAPTCHA_SECRET_KEY', '')),
        'meta_title': 'Catálogo de productos | REMSA Plásticos',
        'meta_description': 'Consulta productos REMSA y descarga la ficha de cada producto con la información publicada en nuestro catálogo.',
    }
    return render(request, 'catalogo/lista.html', contexto)


def detalle_producto(request, slug):
    producto = get_object_or_404(
        Producto.objects.select_related('categoria').prefetch_related(
            'galeria', 'especificaciones'
        ),
        slug=slug,
        activo=True,
        categoria__nombre__in=PUBLIC_CATALOG_CATEGORIES,
    )
    producto = _annotate_catalogue_products([producto])[0]
    relacionados = Producto.objects.filter(
        categoria=producto.categoria,
        activo=True,
        en_catalogo=True,
        categoria__nombre__in=PUBLIC_CATALOG_CATEGORIES,
    ).exclude(pk=producto.pk)[:4]

    contexto = {
        'producto': producto,
        'relacionados': relacionados,
        'mostrar_ficha_pdf': False,
        'meta_title': f'{producto.nombre} | REMSA Plásticos',
        'meta_description': producto.descripcion_corta,
    }
    return render(request, 'catalogo/detalle.html', contexto)


def _pdf_paragraph(text, style):
    safe_text = escape(str(text)).replace('\n', '<br/>')
    return Paragraph(safe_text, style)


def _pdf_image(path, max_width, max_height, max_pixels=(1400, 1100)):
    image_buffer = BytesIO()
    with PillowImage.open(path) as source:
        source.thumbnail(max_pixels, PillowImage.Resampling.LANCZOS)
        transparent = source.mode in ('RGBA', 'LA') or 'transparency' in source.info
        image = source.convert('RGBA' if transparent else 'RGB')
        image.save(
            image_buffer,
            format='PNG' if transparent else 'JPEG',
            optimize=True,
            **({} if transparent else {'quality': 84}),
        )

    image_buffer.seek(0)
    image_width, image_height = ImageReader(image_buffer).getSize()
    image_buffer.seek(0)
    scale = min(max_width / image_width, max_height / image_height)
    return Image(
        image_buffer,
        width=image_width * scale,
        height=image_height * scale,
    )


def ficha_producto_pdf(_request, slug):
    producto = get_object_or_404(
        Producto.objects.prefetch_related('especificaciones'),
        slug=slug,
        activo=True,
        categoria__nombre__in=PUBLIC_CATALOG_CATEGORIES,
    )
    producto = _annotate_catalogue_products([producto])[0]

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=22 * mm,
        title=f'Ficha de producto - {producto.nombre}',
        author='REMSA Plásticos',
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ProductTitle',
        parent=styles['Title'],
        textColor=colors.HexColor('#123253'),
        fontName='Helvetica-Bold',
        fontSize=19,
        leading=24,
        alignment=0,
        spaceAfter=7 * mm,
    )
    label_style = ParagraphStyle(
        'ProductLabel',
        parent=styles['BodyText'],
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#123253'),
        fontSize=9,
        leading=13,
    )
    value_style = ParagraphStyle(
        'ProductValue',
        parent=styles['BodyText'],
        textColor=colors.HexColor('#344256'),
        fontSize=9,
        leading=13,
    )
    story = []

    logo_path = settings.BASE_DIR / 'static' / 'img' / 'logo' / 'logo_remsa.png'
    if logo_path.is_file():
        story.append(_pdf_image(logo_path, 52 * mm, 20 * mm, max_pixels=(700, 500)))
    story.extend([
        Spacer(1, 7 * mm),
        _pdf_paragraph('FICHA DE PRODUCTO', styles['Heading3']),
        Spacer(1, 2 * mm),
        _pdf_paragraph(producto.nombre, title_style),
    ])

    if producto.descripcion_corta:
        story.extend([
            _pdf_paragraph('Descripción', label_style),
            Spacer(1, 1.5 * mm),
            _pdf_paragraph(producto.descripcion_corta, value_style),
            Spacer(1, 5 * mm),
        ])

    fields = [
        ('Capacidad / medida', producto.capacidad),
        ('Color', producto.color),
        ('Tipo', producto.get_tipo_display()),
        ('Especificaciones técnicas', producto.catalogo_especificaciones),
    ]
    rows = [
        [_pdf_paragraph(label, label_style), _pdf_paragraph(value, value_style)]
        for label, value in fields if value
    ]
    if rows:
        table = Table(rows, colWidths=[48 * mm, document.width - 48 * mm], hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#d7e0e9')),
            ('INNERGRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#d7e0e9')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
        ]))
        story.append(table)

    if producto.imagen_principal:
        image_path = Path(producto.imagen_principal.path)
        if image_path.is_file():
            story.extend([
                Spacer(1, 8 * mm),
                _pdf_image(image_path, 150 * mm, 75 * mm),
            ])

    def draw_footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor('#d7e0e9'))
        canvas.line(doc.leftMargin, 16 * mm, A4[0] - doc.rightMargin, 16 * mm)
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#64748b'))
        canvas.drawRightString(
            A4[0] - doc.rightMargin,
            11 * mm,
            f'REMSA Plásticos | {doc.page}',
        )
        canvas.restoreState()

    document.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)
    buffer.seek(0)
    filename = f'ficha-{slugify(producto.nombre) or "producto"}.pdf'
    return FileResponse(
        buffer,
        as_attachment=True,
        filename=filename,
        content_type='application/pdf',
    )


def lista_servicios(request):
    servicios = Servicio.objects.filter(activo=True)
    contexto = {
        'servicios': servicios,
        'meta_title': 'Soluciones: pigmentado, personalización y protección UV | REMSA Plásticos',
        'meta_description': 'Conoce las soluciones de personalización de garrafones, pigmentado de envases y más de REMSA Plásticos.',
    }
    return render(request, 'catalogo/servicios.html', contexto)


def detalle_servicio(request, slug):
    servicio = get_object_or_404(Servicio, slug=slug, activo=True)
    contexto = {
        'servicio': servicio,
        'meta_title': f'{servicio.nombre} | REMSA Plásticos',
        'meta_description': servicio.descripcion_corta,
    }
    return render(request, 'catalogo/servicio_detalle.html', contexto)
