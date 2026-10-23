from django.db import migrations
from django.utils.text import slugify


def _es_pead(producto):
    textos = [
        producto.nombre, producto.tipo, producto.material,
        producto.descripcion_corta, producto.descripcion,
    ]
    textos += [f'{e.nombre} {e.valor}' for e in producto.especificaciones.all()]
    texto = ' '.join(textos).casefold()
    return 'pead' in texto or 'hdpe' in texto


def separar_garrafas(apps, schema_editor):
    Categoria = apps.get_model('catalogo', 'Categoria')
    Producto = apps.get_model('catalogo', 'Producto')
    original = Categoria.objects.filter(nombre__iexact='Garrafas').first()
    if original is None:
        return

    destinos = {}
    for orden, nombre in enumerate(('Garrafas PET', 'Garrafas PEAD')):
        destinos[nombre], _ = Categoria.objects.get_or_create(
            nombre=nombre,
            defaults={
                'slug': slugify(nombre),
                'orden': original.orden + orden,
                'activo': original.activo,
                'descripcion': f'Garrafas de {nombre.split()[-1]}.',
            },
        )

    for producto in Producto.objects.filter(categoria=original).prefetch_related('especificaciones'):
        producto.categoria = destinos['Garrafas PEAD' if _es_pead(producto) else 'Garrafas PET']
        producto.save(update_fields=['categoria'])

    original.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('catalogo', '0005_descripcion_frasco_pet_250ml'),
    ]

    operations = [
        migrations.RunPython(separar_garrafas, migrations.RunPython.noop),
    ]
