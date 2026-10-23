from django.db import migrations


def add_frasco_250ml(apps, schema_editor):
    Categoria = apps.get_model('catalogo', 'Categoria')
    Producto = apps.get_model('catalogo', 'Producto')
    EspecificacionProducto = apps.get_model('catalogo', 'EspecificacionProducto')

    categoria = Categoria.objects.filter(nombre__iexact='Frascos').first()
    if categoria is None:
        categoria = Categoria.objects.create(nombre='Frascos', slug='frascos')

    producto = (
        Producto.objects.filter(categoria=categoria, nombre__icontains='250').first()
        or Producto.objects.filter(slug='frasco-250-ml').first()
    )
    if producto is None:
        producto = Producto.objects.create(
            nombre='FRASCO 250 ML',
            slug='frasco-250-ml',
            categoria=categoria,
            tipo='Botella PET',
        )

    producto.material = 'PET'
    producto.capacidad = '250 ml'
    producto.color = 'Transparente, Azul, Verde, Ámbar'
    producto.activo = True
    producto.en_catalogo = True
    producto.save()

    # La ficha se define solo con estos datos; se reemplazan filas previas.
    EspecificacionProducto.objects.filter(producto=producto).delete()
    especificaciones = [
        ('Modelo', '250 - 63'),
        ('Peso', '19 g'),
        ('Tipo de boca', '63-400'),
        ('Tipo de empaque', 'Bolsa de plástico'),
        ('Contenido por empaque', '119 pzas'),
    ]
    for orden, (nombre, valor) in enumerate(especificaciones, start=1):
        EspecificacionProducto.objects.create(
            producto=producto, nombre=nombre, valor=valor, orden=orden,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('catalogo', '0003_detalles_botella_pet_148ml'),
    ]

    operations = [
        migrations.RunPython(add_frasco_250ml, migrations.RunPython.noop),
    ]
