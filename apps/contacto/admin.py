from django.contrib import admin
from .models import MensajeContacto


@admin.register(MensajeContacto)
class MensajeContactoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'empresa', 'correo', 'asunto', 'atendido', 'creado_en')
    list_editable = ('atendido',)
    list_filter = ('atendido', 'creado_en')
    search_fields = ('nombre', 'empresa', 'correo', 'mensaje')
    readonly_fields = ('ip_origen', 'creado_en')
