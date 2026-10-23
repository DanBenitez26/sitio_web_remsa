from django.contrib import admin
from .models import Categoria, Producto, ImagenProducto, EspecificacionProducto, Servicio


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'orden', 'activo')
    list_editable = ('orden', 'activo')
    prepopulated_fields = {'slug': ('nombre',)}
    search_fields = ('nombre',)


class ImagenProductoInline(admin.TabularInline):
    model = ImagenProducto
    extra = 1


class EspecificacionProductoInline(admin.TabularInline):
    model = EspecificacionProducto
    extra = 1
    verbose_name = 'Especificación del producto'
    verbose_name_plural = 'Especificaciones adicionales del producto'


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'tipo', 'material', 'capacidad', 'activo', 'en_catalogo', 'destacado', 'orden')
    list_editable = ('orden', 'activo', 'destacado')
    list_filter = ('categoria', 'tipo', 'material', 'activo', 'en_catalogo', 'destacado')
    search_fields = ('nombre', 'descripcion_corta', 'descripcion', 'aplicaciones')
    prepopulated_fields = {'slug': ('nombre',)}
    inlines = [ImagenProductoInline, EspecificacionProductoInline]
    fieldsets = (
        (None, {'fields': ('nombre', 'slug', 'categoria', 'tipo')}),
        (
            'Descripción',
            {
                'description': (
                    'La descripción se muestra en «Ver detalles». Usa la descripción '
                    'breve de la hoja de cálculo o agrega una descripción propia en '
                    'el campo de texto largo.'
                ),
                'fields': ('descripcion_corta', 'descripcion', 'aplicaciones'),
            },
        ),
        ('Características', {'fields': ('material', 'capacidad', 'color')}),
        ('Imagen y estado', {'fields': ('imagen_principal', 'activo', 'en_catalogo', 'destacado', 'orden')}),
    )


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'orden', 'activo')
    list_editable = ('orden', 'activo')
    prepopulated_fields = {'slug': ('nombre',)}
    search_fields = ('nombre',)
