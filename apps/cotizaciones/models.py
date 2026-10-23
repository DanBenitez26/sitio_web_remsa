import uuid
from django.db import models
from django.utils import timezone


class Cliente(models.Model):
    ESTADO_CHOICES = [
        ('PROSPECTO', 'Prospecto'),
        ('ACTIVO', 'Cliente activo'),
        ('INACTIVO', 'Inactivo'),
    ]

    nombre = models.CharField(max_length=150)
    empresa = models.CharField(max_length=150, blank=True)
    correo = models.EmailField()
    telefono = models.CharField(max_length=30, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PROSPECTO')
    responsable = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='clientes_asignados'
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['-creado_en']

    def __str__(self):
        return f'{self.nombre} ({self.empresa})' if self.empresa else self.nombre


class Seguimiento(models.Model):
    TIPO_CHOICES = [
        ('LLAMADA', 'Llamada'),
        ('CORREO', 'Correo'),
        ('WHATSAPP', 'WhatsApp'),
        ('REUNION', 'Reunión'),
        ('NOTA', 'Nota interna'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='seguimientos')
    solicitud = models.ForeignKey(
        'SolicitudCotizacion', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='seguimientos'
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='NOTA')
    fecha = models.DateTimeField(default=timezone.now)
    nota = models.TextField(help_text='Describe el contacto, acuerdo o avance del cliente')
    proximo_contacto = models.DateField(null=True, blank=True)
    creado_por = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='seguimientos_creados'
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Seguimiento'
        verbose_name_plural = 'Seguimientos'
        ordering = ['-fecha', '-creado_en']

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.cliente}'


def _generar_folio():
    fecha = timezone.now().strftime('%Y%m%d')
    sufijo = uuid.uuid4().hex[:5].upper()
    return f'REMSA-{fecha}-{sufijo}'


class SolicitudCotizacion(models.Model):
    ESTADO_CHOICES = [
        ('NUEVA', 'Nueva'),
        ('EN_PROCESO', 'En proceso'),
        ('ATENDIDA', 'Atendida'),
    ]

    folio = models.CharField(max_length=40, unique=True, default=_generar_folio, editable=False)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='solicitudes')
    mensaje = models.TextField(blank=True, help_text='Comentarios adicionales del cliente')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='NUEVA')
    ip_origen = models.GenericIPAddressField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Solicitud de Cotización'
        verbose_name_plural = 'Solicitudes de Cotización'
        ordering = ['-creado_en']

    def __str__(self):
        return self.folio


class ItemCotizacion(models.Model):
    solicitud = models.ForeignKey(SolicitudCotizacion, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey('catalogo.Producto', on_delete=models.PROTECT, related_name='items_cotizados')
    cantidad = models.PositiveIntegerField(default=1)
    notas = models.CharField(max_length=250, blank=True)

    class Meta:
        verbose_name = 'Item de Cotización'
        verbose_name_plural = 'Items de Cotización'

    def __str__(self):
        return f'{self.cantidad} x {self.producto.nombre}'
