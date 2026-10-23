from django.db import models


class Banner(models.Model):
    titulo = models.CharField(max_length=150)
    subtitulo = models.CharField(max_length=250, blank=True)
    imagen = models.ImageField(upload_to='banners/', blank=True, null=True)
    cta_texto = models.CharField(max_length=50, blank=True, default='Ver catálogo')
    cta_url = models.CharField(max_length=200, blank=True, default='/catalogo/')
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Banner'
        verbose_name_plural = 'Banners'
        ordering = ['orden']

    def __str__(self):
        return self.titulo


class Testimonio(models.Model):
    nombre = models.CharField(max_length=120)
    empresa = models.CharField(max_length=150, blank=True)
    contenido = models.TextField()
    calificacion = models.PositiveSmallIntegerField(default=5, help_text='1 a 5')
    activo = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Testimonio'
        verbose_name_plural = 'Testimonios'
        ordering = ['orden']

    def __str__(self):
        return f'{self.nombre} ({self.empresa})'
