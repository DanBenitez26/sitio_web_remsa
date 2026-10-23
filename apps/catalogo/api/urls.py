from rest_framework.routers import DefaultRouter
from .views import CategoriaViewSet, ProductoViewSet, ServicioViewSet

router = DefaultRouter()
router.register('categorias', CategoriaViewSet, basename='api-categorias')
router.register('productos', ProductoViewSet, basename='api-productos')
router.register('servicios', ServicioViewSet, basename='api-servicios')

urlpatterns = router.urls
