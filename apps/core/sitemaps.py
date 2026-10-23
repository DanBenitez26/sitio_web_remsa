from django.contrib.sitemaps import Sitemap
from apps.catalogo.catalogue import PUBLIC_CATALOG_CATEGORIES
from apps.catalogo.models import Producto, Categoria, Servicio


class ProductoSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Producto.objects.filter(
            activo=True,
            en_catalogo=True,
            categoria__nombre__in=PUBLIC_CATALOG_CATEGORIES,
        )

    def location(self, obj):
        return obj.get_absolute_url()


class CategoriaSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.6

    def items(self):
        return Categoria.objects.filter(
            activo=True,
            nombre__in=PUBLIC_CATALOG_CATEGORIES,
            productos__activo=True,
            productos__en_catalogo=True,
        ).distinct()

    def location(self, obj):
        return obj.get_absolute_url()


class ServicioSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5

    def items(self):
        return Servicio.objects.filter(activo=True)

    def location(self, obj):
        return obj.get_absolute_url()


class StaticViewSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.9

    def items(self):
        return ['paginas:home', 'paginas:nosotros', 'contacto:contacto', 'catalogo:lista', 'catalogo:servicios']

    def location(self, item):
        from django.urls import reverse
        return reverse(item)
