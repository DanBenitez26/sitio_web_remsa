from django.db import models


class ConfiguracionSitio(models.Model):
    """
    Configuracion global del sitio (singleton: solo debe existir un registro).
    Editable desde Django Admin sin tocar codigo. Se inyecta en todas las
    plantillas mediante apps.core.context_processors.configuracion_sitio.
    """
    nombre_empresa = models.CharField(max_length=150, default='REMSA Plásticos')
    eslogan = models.CharField(
        max_length=200, blank=True,
        default='Fabricación nacional de envases y empaques de plástico'
    )
    telefono_principal = models.CharField(max_length=30, blank=True, help_text='Ej. 999 000 0000')
    telefono_secundario = models.CharField(max_length=30, blank=True, help_text='Teléfono adicional de contacto')
    whatsapp_numero = models.CharField(
        max_length=30, blank=True,
        help_text='Solo dígitos con código de país, ej. 5219990000000, usado para el botón flotante de WhatsApp'
    )
    correo_comercial = models.EmailField(blank=True)
    correo_notificaciones = models.EmailField(
        blank=True, help_text='Correo interno que recibe las nuevas solicitudes de cotización y mensajes de contacto'
    )
    direccion = models.TextField(blank=True, help_text='Dirección completa mostrada en Contacto y footer')
    horario_atencion = models.CharField(
        max_length=200, blank=True, default='Lunes a viernes'
    )
    mapa_embed_url = models.URLField(
        blank=True, help_text='URL de embed de Google Maps (iframe src) para la página de Contacto'
    )
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    anio_fundacion = models.PositiveIntegerField(default=1994)
    texto_footer = models.TextField(
        blank=True,
        help_text='Texto corto institucional para el footer (opcional)'
    )

    class Meta:
        verbose_name = 'Configuración del Sitio'
        verbose_name_plural = 'Configuración del Sitio'

    def __str__(self):
        return self.nombre_empresa

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
