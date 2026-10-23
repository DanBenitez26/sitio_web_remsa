from django.urls import path
from . import views

app_name = 'catalogo'

urlpatterns = [
    path('', views.lista_productos, name='lista'),
    path('servicios/', views.lista_servicios, name='servicios'),
    path('servicios/<slug:slug>/', views.detalle_servicio, name='servicio_detalle'),
    path('<slug:slug>/ficha.pdf', views.ficha_producto_pdf, name='ficha_pdf'),
    path('<slug:slug>/', views.detalle_producto, name='detalle'),
]
