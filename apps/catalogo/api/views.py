from rest_framework import viewsets
from apps.catalogo.catalogue import PUBLIC_CATALOG_CATEGORIES
from apps.catalogo.models import Categoria, Producto, Servicio
from .serializers import CategoriaSerializer, ProductoSerializer, ServicioSerializer


class CategoriaViewSet(viewsets.ReadOnlyModelViewSet):
    """Solo lectura: el catalogo se administra desde Django Admin, no vía API publica."""
    queryset = Categoria.objects.filter(
        activo=True,
        nombre__in=PUBLIC_CATALOG_CATEGORIES,
        productos__activo=True,
        productos__en_catalogo=True,
    ).distinct()
    serializer_class = CategoriaSerializer


class ProductoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Producto.objects.filter(
        activo=True,
        en_catalogo=True,
        categoria__nombre__in=PUBLIC_CATALOG_CATEGORIES,
    ).select_related('categoria').prefetch_related('especificaciones', 'galeria')
    serializer_class = ProductoSerializer
    filterset_fields = ['categoria__slug', 'material', 'tipo']

    def get_queryset(self):
        qs = super().get_queryset()
        categoria = self.request.query_params.get('categoria')
        if categoria:
            qs = qs.filter(categoria__slug=categoria)
        return qs


class ServicioViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Servicio.objects.filter(activo=True)
    serializer_class = ServicioSerializer
