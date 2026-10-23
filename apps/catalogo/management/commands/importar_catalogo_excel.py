from collections import defaultdict
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from openpyxl import load_workbook

from apps.catalogo.catalogue import PUBLIC_CATALOG_CATEGORY_KEYS, split_garrafas_category
from apps.catalogo.models import Categoria, EspecificacionProducto, Producto


HEADERS = (
    'Categoría',
    'Nombre del producto',
    'Descripción',
    'Capacidad / medida',
    'Color',
    'Tipo',
    'Especificaciones técnicas',
    'Aplicaciones',
    'Variante',
)


def _text(value):
    return '' if value is None else str(value).strip()


def _key(value):
    return ' '.join(value.split()).casefold()


class Command(BaseCommand):
    help = 'Importa o actualiza el catálogo REMSA desde la hoja Catalogo de un Excel.'

    def add_arguments(self, parser):
        parser.add_argument('archivo', type=Path, help='Ruta al archivo Excel del catálogo.')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Valida el archivo y muestra el resumen sin modificar la base de datos.',
        )

    def handle(self, *_args, **options):
        path = options['archivo']
        if not path.is_file():
            raise CommandError(f'No se encontró el archivo Excel: {path}')

        workbook = load_workbook(path, read_only=True, data_only=True)
        try:
            if 'Catalogo' not in workbook.sheetnames:
                raise CommandError('El libro debe contener una hoja llamada "Catalogo".')

            sheet = workbook['Catalogo']
            headers = tuple(_text(value) for value in next(
                sheet.iter_rows(min_row=1, max_row=1, values_only=True)
            ))
            if headers[:len(HEADERS)] != HEADERS:
                raise CommandError(
                    'Los encabezados de la hoja "Catalogo" no coinciden con el formato esperado.'
                )

            records = []
            seen_names = set()
            for row_number, values in enumerate(
                sheet.iter_rows(min_row=2, max_col=len(HEADERS), values_only=True),
                start=2,
            ):
                values = tuple(_text(value) for value in values)
                if not any(values):
                    continue

                record = dict(zip(HEADERS, values))
                record['Categoría'] = split_garrafas_category(
                    record['Categoría'],
                    record['Nombre del producto'],
                    record['Tipo'],
                    record['Descripción'],
                    record['Especificaciones técnicas'],
                    record['Variante'],
                )
                name = record['Nombre del producto']
                if not name:
                    raise CommandError(f'Falta el nombre del producto en la fila {row_number}.')
                if not record['Categoría'] or not record['Tipo']:
                    raise CommandError(
                        f'La categoría y el tipo son obligatorios en la fila {row_number}.'
                    )

                name_key = _key(name)
                if name_key in seen_names:
                    raise CommandError(f'El producto "{name}" está duplicado en el Excel.')
                seen_names.add(name_key)

                limits = {
                    'Categoría': 100,
                    'Nombre del producto': 150,
                    'Descripción': 220,
                    'Capacidad / medida': 100,
                    'Color': 100,
                    'Tipo': 40,
                    'Especificaciones técnicas': 150,
                    'Variante': 150,
                }
                for field, limit in limits.items():
                    if len(record[field]) > limit:
                        raise CommandError(
                            f'El valor de "{field}" excede {limit} caracteres en la fila {row_number}.'
                        )
                records.append(record)
        finally:
            workbook.close()

        if not records:
            raise CommandError('La hoja "Catalogo" no contiene productos para importar.')

        categories = sorted({record['Categoría'] for record in records}, key=str.casefold)
        if options['dry_run']:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Validación correcta: {len(records)} productos y '
                    f'{len(categories)} categorías. No se modificó la base de datos.'
                )
            )
            return

        with transaction.atomic():
            existing_products = defaultdict(list)
            for product in Producto.objects.all().only('id', 'nombre'):
                existing_products[_key(product.nombre)].append(product)

            products_by_name = {}
            for record in records:
                matches = existing_products.get(_key(record['Nombre del producto']), [])
                if len(matches) > 1:
                    raise CommandError(
                        f'Hay varios productos existentes con el nombre '
                        f'"{record["Nombre del producto"]}".'
                    )
                if matches:
                    products_by_name[_key(record['Nombre del producto'])] = matches[0]

            categories_by_name = {
                _key(category.nombre): category
                for category in Categoria.objects.all()
            }
            imported_ids = []
            for order, record in enumerate(records):
                category_key = _key(record['Categoría'])
                category = categories_by_name.get(category_key)
                if category is None:
                    category = Categoria.objects.create(nombre=record['Categoría'])
                    categories_by_name[category_key] = category

                product_key = _key(record['Nombre del producto'])
                product = products_by_name.get(product_key, Producto())
                product.nombre = record['Nombre del producto']
                product.categoria = category
                product.tipo = record['Tipo']
                product.descripcion_corta = record['Descripción']
                product.material = ''
                product.capacidad = record['Capacidad / medida']
                product.color = record['Color']
                product.aplicaciones = record['Aplicaciones']
                product.activo = True
                product.en_catalogo = (
                    _key(record['Categoría']) in PUBLIC_CATALOG_CATEGORY_KEYS
                )
                product.orden = order
                product.save()
                for specification_name, field_name in (
                    ('Especificaciones técnicas', 'Especificaciones técnicas'),
                    ('Variante', 'Variante'),
                ):
                    imported_specs = product.especificaciones.filter(
                        nombre=specification_name,
                    )
                    value = record[field_name]
                    if value:
                        system_spec = imported_specs.first()
                        if system_spec:
                            system_spec.valor = value
                            system_spec.save(update_fields=['valor'])
                            imported_specs.exclude(pk=system_spec.pk).delete()
                        else:
                            EspecificacionProducto.objects.create(
                                producto=product,
                                nombre=specification_name,
                                valor=value,
                            )
                    else:
                        imported_specs.delete()
                imported_ids.append(product.pk)

            Producto.objects.exclude(pk__in=imported_ids).update(en_catalogo=False)

        self.stdout.write(
            self.style.SUCCESS(
                f'Catálogo actualizado: {len(imported_ids)} productos importados '
                f'en {len(categories)} categorías. Los demás productos se conservaron '
                'en la base de datos, pero ya no aparecen en el catálogo público.'
            )
        )
