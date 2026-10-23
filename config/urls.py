"""
URLs raíz. Cada app tiene su propio urls.py; aquí solo se enlazan bajo un prefijo.
En fases posteriores se agregarán aquí: sitemap.xml, robots.txt y la API DRF.
"""
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

from apps.core.sitemaps import ProductoSitemap, CategoriaSitemap, ServicioSitemap, StaticViewSitemap

sitemaps = {
    'productos': ProductoSitemap,
    'categorias': CategoriaSitemap,
    'servicios': ServicioSitemap,
    'paginas': StaticViewSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.paginas.urls')),
    path('catalogo/', include('apps.catalogo.urls')),
    path('cotizacion/', include('apps.cotizaciones.urls')),
    path('contacto/', include('apps.contacto.urls')),
    path('api/', include('apps.core.urls')),
    path('api/catalogo/', include('apps.catalogo.api.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
]

# Servir archivos de media en desarrollo (en producción lo hace el servidor web / whitenoise para static)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Pruebas en Render: se sirven las imágenes del repo (disco efímero; migrar a S3/Cloudinary para producción final)
    from django.urls import re_path
    from django.views.static import serve
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
