from django.urls import path
from . import views

app_name = 'contacto'

urlpatterns = [
    path('', views.contacto, name='contacto'),
    path('centroamerica/enviar/', views.contacto_centroamerica, name='contacto_centroamerica'),
    path('chatbot/solicitar-contacto/', views.chatbot_lead, name='chatbot_lead'),
    path('solicitar-catalogo/', views.solicitar_catalogo, name='solicitar_catalogo'),
]
