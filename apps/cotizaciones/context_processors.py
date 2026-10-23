"""Expone el numero de productos en el carrito de cotizacion a todas las plantillas."""


def carrito_info(request):
    carrito = request.session.get('carrito', {})
    total_items = sum(carrito.values()) if carrito else 0
    return {'carrito_total_items': total_items}
