from django.urls import path
from . import views

app_name = 'paginas'

urlpatterns = [
    path('', views.home, name='home'),
    path('nosotros/', views.nosotros, name='nosotros'),
    path('aviso-de-privacidad/', views.privacidad, name='privacidad'),
    path('terminos-y-condiciones/', views.terminos, name='terminos'),
]
