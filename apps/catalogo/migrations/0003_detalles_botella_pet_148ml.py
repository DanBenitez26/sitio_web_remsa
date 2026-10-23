from django.db import migrations


def add_148ml_details(apps, schema_editor):
    Producto = apps.get_model('catalogo', 'Producto')
    EspecificacionProducto = apps.get_model('catalogo', 'EspecificacionProducto')

    producto = Producto.objects.filter(
        slug='botella-pet-148ml-148-24-transparente',
    ).first()
    if producto is None:
        return

    if not producto.descripcion:
        producto.descripcion = (
            'Diseñada para envasar condimentos líquidos y espesos, como salsas, '
            'chile y aceites. Su cuello largo y angosto brinda mayor control al servir.'
        )
        producto.save(update_fields=['descripcion'])

    especificaciones = {
        'Peso': '19 g',
        'Altura': '169.5 mm',
        'Ancho': '43.2 mm',
        'Rosca': 'Tapa de rosca 24 mm',
        'Capacidad nominal': '148 ml',
        'Capacidad de derrame': '148 ml',
    }
    for nombre, valor in especificaciones.items():
        EspecificacionProducto.objects.get_or_create(
            producto=producto,
            nombre=nombre,
            defaults={'valor': valor, 'orden': 10},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('catalogo', '0002_producto_en_catalogo_alter_producto_material_and_more'),
    ]

    operations = [
        migrations.RunPython(add_148ml_details, migrations.RunPython.noop),
    ]
