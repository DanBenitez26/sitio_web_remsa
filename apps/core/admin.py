from django.contrib import admin
from .models import ConfiguracionSitio


@admin.register(ConfiguracionSitio)
class ConfiguracionSitioAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Identidad', {'fields': ('nombre_empresa', 'eslogan', 'anio_fundacion')}),
        ('Contacto', {'fields': (
            'telefono_principal', 'telefono_secundario', 'whatsapp_numero',
            'correo_comercial', 'correo_notificaciones',
            'direccion', 'horario_atencion', 'mapa_embed_url',
        )}),
        ('Redes sociales', {'fields': ('facebook_url', 'instagram_url', 'linkedin_url')}),
        ('Footer', {'fields': ('texto_footer',)}),
    )

    def has_add_permission(self, request):
        # Patron singleton: no permitir crear un segundo registro
        return not ConfiguracionSitio.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
