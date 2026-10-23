from django.db import models


class MensajeContacto(models.Model):
    nombre = models.CharField(max_length=150)
    empresa = models.CharField(max_length=150, blank=True)
    correo = models.EmailField()
    telefono = models.CharField(max_length=30, blank=True)
    asunto = models.CharField(max_length=150, blank=True)
    mensaje = models.TextField()
    ip_origen = models.GenericIPAddressField(blank=True, null=True)
    atendido = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Mensaje de Contacto'
        verbose_name_plural = 'Mensajes de Contacto'
        ordering = ['-creado_en']

    def __str__(self):
        return f'{self.nombre} - {self.asunto or "Sin asunto"}'
