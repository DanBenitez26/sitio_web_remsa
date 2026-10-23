from django.db import migrations

DESCRIPCION = (
    'Para la producción del modelo 63 se utiliza material PET 100% virgen. '
    'Con un alto de 84.4 mm y paredes lisas transparentes, un ancho de 72 mm '
    'y tapa 63-400, con el sello de calidad de REMSA.'
)


def set_descripcion(apps, schema_editor):
    Producto = apps.get_model('catalogo', 'Producto')
    Producto.objects.filter(
        categoria__nombre__iexact='Frascos', nombre__icontains='250',
    ).update(descripcion=DESCRIPCION)


class Migration(migrations.Migration):

    dependencies = [
        ('catalogo', '0004_detalles_frasco_pet_250ml'),
    ]

    operations = [
        migrations.RunPython(set_descripcion, migrations.RunPython.noop),
    ]
