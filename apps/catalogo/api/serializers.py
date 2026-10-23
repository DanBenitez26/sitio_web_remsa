from rest_framework import serializers
from apps.catalogo.ficha import build_ficha
from apps.catalogo.models import Categoria, Producto, EspecificacionProducto, ImagenProducto, Servicio


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'slug', 'descripcion']


class EspecificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EspecificacionProducto
        fields = ['nombre', 'valor']


class ImagenProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagenProducto
        fields = ['imagen', 'alt_text']


class ProductoSerializer(serializers.ModelSerializer):
    categoria = CategoriaSerializer(read_only=True)
    especificaciones = EspecificacionSerializer(many=True, read_only=True)
    galeria = ImagenProductoSerializer(many=True, read_only=True)
    ficha_tecnica = serializers.SerializerMethodField()
    imagen_principal = serializers.SerializerMethodField()

    def get_imagen_principal(self, producto):
        imagen = producto.imagen_catalogo
        if not imagen:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(imagen.url) if request else imagen.url
    class Meta:
        model = Producto
        fields = [
            'id', 'nombre', 'slug', 'categoria', 'tipo', 'descripcion_corta',
            'descripcion', 'material', 'capacidad', 'color', 'aplicaciones',
            'imagen_principal', 'especificaciones', 'galeria', 'ficha_tecnica',
            'creado_en',
        ]

    def get_ficha_tecnica(self, producto):
        return build_ficha(producto)


class ServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servicio
        fields = ['id', 'nombre', 'slug', 'descripcion_corta', 'descripcion', 'icono']
