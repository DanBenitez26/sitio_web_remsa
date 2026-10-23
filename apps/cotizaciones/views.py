from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.urls import reverse

from apps.catalogo.models import Producto
from apps.core.utils import excede_limite_envios, obtener_ip_cliente
from .forms import SolicitudCotizacionForm
from .models import SolicitudCotizacion
from . import services

CARRITO_SESSION_KEY = 'carrito'


def _get_carrito(request):
    return request.session.get(CARRITO_SESSION_KEY, {})


def _guardar_carrito(request, carrito):
    request.session[CARRITO_SESSION_KEY] = carrito
    request.session.modified = True


@require_POST
def agregar_al_carrito(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id, activo=True)
    cantidad = int(request.POST.get('cantidad', 1) or 1)
    cantidad = max(1, cantidad)

    carrito = _get_carrito(request)
    clave = str(producto.pk)
    carrito[clave] = carrito.get(clave, 0) + cantidad
    _guardar_carrito(request, carrito)

    messages.success(request, f'"{producto.nombre}" se agregó a tu solicitud de cotización.')
    siguiente = request.POST.get('next') or reverse('cotizaciones:carrito')
    return redirect(siguiente)


@require_POST
def actualizar_carrito(request, producto_id):
    carrito = _get_carrito(request)
    clave = str(producto_id)
    cantidad = int(request.POST.get('cantidad', 1) or 1)
    if clave in carrito:
        if cantidad <= 0:
            carrito.pop(clave)
        else:
            carrito[clave] = cantidad
        _guardar_carrito(request, carrito)
    return redirect('cotizaciones:carrito')


@require_POST
def eliminar_del_carrito(request, producto_id):
    carrito = _get_carrito(request)
    carrito.pop(str(producto_id), None)
    _guardar_carrito(request, carrito)
    messages.info(request, 'Producto eliminado de tu solicitud.')
    return redirect('cotizaciones:carrito')


def ver_carrito(request):
    carrito = _get_carrito(request)
    productos = Producto.objects.filter(pk__in=carrito.keys(), activo=True)
    items = [
        {'producto': producto, 'cantidad': carrito.get(str(producto.pk), 1)}
        for producto in productos
    ]

    if request.method == 'POST':
        form = SolicitudCotizacionForm(request.POST)
        if not items:
            messages.error(request, 'Agrega al menos un producto antes de enviar tu solicitud.')
        elif excede_limite_envios(request, 'cotizacion'):
            messages.error(request, 'Has enviado demasiadas solicitudes en poco tiempo. Intenta de nuevo más tarde.')
        elif form.is_valid():
            cliente = form.guardar_cliente()
            solicitud, _ = services.crear_solicitud_desde_carrito(
                cliente=cliente,
                mensaje=form.cleaned_data.get('mensaje', ''),
                carrito=carrito,
                ip_origen=obtener_ip_cliente(request),
            )
            services.notificar_nueva_solicitud(solicitud)
            _guardar_carrito(request, {})
            return redirect('cotizaciones:confirmacion', folio=solicitud.folio)
    else:
        form = SolicitudCotizacionForm()

    return render(request, 'cotizaciones/carrito.html', {
        'items': items,
        'form': form,
        'total_productos': len(items),
    })


def confirmacion(request, folio):
    solicitud = get_object_or_404(SolicitudCotizacion, folio=folio)
    return render(request, 'cotizaciones/confirmacion.html', {'solicitud': solicitud})
