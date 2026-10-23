from django.shortcuts import render

from apps.catalogo.models import Producto, Servicio, Categoria
from .models import Banner, Testimonio


def home(request):
    contexto = {
        'banners': Banner.objects.filter(activo=True),
        'productos_destacados': Producto.objects.filter(activo=True, destacado=True)[:8],
        'servicios': Servicio.objects.filter(activo=True)[:4],
        'categorias': Categoria.objects.filter(activo=True),
        'testimonios': Testimonio.objects.filter(activo=True),
        'meta_title': 'REMSA Plásticos | Fabricación de envases y empaques de plástico',
        'meta_description': (
            'REMSA Plásticos fabrica envases y empaques de PET, PEAD / HDPE y PP: '
            'preformas, botellas, garrafones y tapas, con atención comercial directa.'
        ),
    }
    return render(request, 'home/home.html', contexto)


def nosotros(request):
    contexto = {
        'meta_title': 'Nosotros | REMSA Plásticos',
        'meta_description': 'Historia, misión, visión y valores de REMSA Plásticos, fabricante de envases desde 1994.',
    }
    return render(request, 'paginas/nosotros.html', contexto)


def privacidad(request):
    return render(request, 'legal/privacidad.html', {'meta_title': 'Aviso de Privacidad | REMSA Plásticos'})


def terminos(request):
    return render(request, 'legal/terminos.html', {'meta_title': 'Términos y Condiciones | REMSA Plásticos'})
