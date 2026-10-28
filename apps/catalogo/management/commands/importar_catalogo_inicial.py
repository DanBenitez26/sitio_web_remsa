
from pathlib import Path

from django.apps import apps
from django.core.management import BaseCommand, call_command
from django.db import transaction
from django.db.models import Count


EXPECTED = {
    "Categoria": 1,
    "Producto": 1,
    "ImagenProducto": 0,
    "EspecificacionProducto": 5,
    "Servicio": 0,
}

EXPECTED_FIXTURE_TOTAL = 552


class Command(BaseCommand):
    help = "Importa el catálogo inicial de REMSA con validaciones de seguridad."

    def handle(self, *args, **options):
        fixture = Path(apps.get_app_config("catalogo").path).parent.parent.parent
        fixture = Path.cwd() / "datos_catalogo.json"

        if not fixture.is_file():
            raise RuntimeError(f"No se encontró el archivo: {fixture}")

        models = {
            model.__name__: model
            for model in apps.get_app_config("catalogo").get_models()
        }

        if set(models) != set(EXPECTED):
            raise RuntimeError(
                f"Modelos inesperados en catalogo: {sorted(models)}. "
                "No se modificó la base de datos."
            )

        counts = {
            name: model.objects.count()
            for name, model in models.items()
        }

        if counts != EXPECTED:
            raise RuntimeError(
                f"Los conteos cambiaron: {counts}. "
                "No se modificó la base de datos."
            )

        # Evitar eliminar productos referenciados por otras aplicaciones.
        for model in apps.get_models():
            if model._meta.app_label == "catalogo":
                continue

            for field in model._meta.get_fields():
                if (
                    getattr(field, "many_to_one", False)
                    and field.is_relation
                    and field.remote_field.model._meta.app_label == "catalogo"
                ):
                    if model.objects.filter(
                        **{f"{field.name}__isnull": False}
                    ).exists():
                        raise RuntimeError(
                            f"Hay registros de {model._meta.label} "
                            f"que referencian el catálogo mediante {field.name}. "
                            "Importación cancelada."
                        )

        import json

        with fixture.open(encoding="utf-8") as file:
            data = json.load(file)

        if len(data) != EXPECTED_FIXTURE_TOTAL:
            raise RuntimeError(
                f"El archivo contiene {len(data)} registros, "
                f"no {EXPECTED_FIXTURE_TOTAL}. Importación cancelada."
            )

        fixture_counts = {}
        for item in data:
            label = item["model"].split(".", 1)[-1]
            fixture_counts[label] = fixture_counts.get(label, 0) + 1

        expected_fixture_counts = {
            "categoria": 13,
            "producto": 223,
            "imagenproducto": 40,
            "especificacionproducto": 273,
            "servicio": 3,
        }

        if fixture_counts != expected_fixture_counts:
            raise RuntimeError(
                f"Contenido inesperado en el archivo: {fixture_counts}"
            )

        with transaction.atomic():
            # Eliminar primero los modelos dependientes del catálogo.
            for model in reversed(list(models.values())):
                model.objects.all().delete()

            call_command("loaddata", str(fixture), verbosity=0)
            call_command("sqlsequencereset", "catalogo", stdout=self.stdout)

            self.stdout.write(self.style.SUCCESS("Catálogo importado."))

            for name, model in models.items():
                self.stdout.write(f"{name}: {model.objects.count()}")

