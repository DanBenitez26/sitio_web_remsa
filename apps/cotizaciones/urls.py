from django.urls import path
from . import views

app_name = 'cotizaciones'

urlpatterns = [
    path('', views.ver_carrito, name='carrito'),
    path('agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar'),
    path('actualizar/<int:producto_id>/', views.actualizar_carrito, name='actualizar'),
    path('eliminar/<int:producto_id>/', views.eliminar_del_carrito, name='eliminar'),
    path('confirmacion/<str:folio>/', views.confirmacion, name='confirmacion'),
]
