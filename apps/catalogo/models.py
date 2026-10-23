from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='categorias/', blank=True, null=True)
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('catalogo:lista') + f'?categoria={self.slug}'


class Producto(models.Model):
    MATERIAL_CHOICES = [
        ('PET', 'PET'),
        ('PEAD', 'PEAD / HDPE'),
        ('PP', 'PP / Polipropileno'),
    ]
    TIPO_CHOICES = [
        ('PREFORMA', 'Preforma'),
        ('BOTELLA', 'Botella'),
        ('GARRAFON', 'Garrafón'),
        ('TAPA', 'Tapa'),
        ('OTRO', 'Otro'),
        ('Botella PET', 'Botella PET'),
        ('Tapa rosca', 'Tapa rosca'),
        ('Garrafón PET', 'Garrafón PET'),
        ('Garrafa', 'Garrafa'),
        ('Asa PEAD', 'Asa PEAD'),
        ('Material reciclado', 'Material reciclado'),
        ('Pigmento / Masterbatch', 'Pigmento / Masterbatch'),
        ('Material de empaque', 'Material de empaque'),
        ('Bolsa', 'Bolsa'),
        ('Resina', 'Resina'),
    ]

    nombre = models.CharField(max_length=150)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, related_name='productos'
    )
    tipo = models.CharField(max_length=40, choices=TIPO_CHOICES, default='OTRO')
    descripcion_corta = models.CharField(
        max_length=220, blank=True,
        help_text='Resumen breve mostrado en las tarjetas del catálogo'
    )
    descripcion = models.TextField(blank=True)
    material = models.CharField(max_length=10, choices=MATERIAL_CHOICES, blank=True, default='')
    capacidad = models.CharField(
        max_length=100, blank=True,
        help_text='Ej. "500 ml", "19 L", "28mm" — texto libre porque varía por línea de producto'
    )
    color = models.CharField(max_length=100, blank=True, help_text='Ej. "Natural / Transparente", "A pigmentar"')
    aplicaciones = models.TextField(
        blank=True, help_text='Usos/industrias sugeridas, ej. agua purificada, aceites, químicos de limpieza'
    )
    imagen_principal = models.ImageField(upload_to='productos/', blank=True, null=True)
    activo = models.BooleanField(default=True)
    en_catalogo = models.BooleanField(
        default=True,
        help_text='Indica si el producto pertenece al catálogo público actual.',
    )
    destacado = models.BooleanField(default=False, help_text='Se muestra en la sección de productos destacados del Home')
    orden = models.PositiveIntegerField(default=0)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.nombre)
            slug = base_slug
            i = 1
            while Producto.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f'{base_slug}-{i}'
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('catalogo:detalle', kwargs={'slug': self.slug})

    @property
    def imagen_catalogo(self):
        """Imagen principal o, si falta, la primera de la galería."""
        if self.imagen_principal:
            return self.imagen_principal
        primera = next(iter(self.galeria.all()), None)
        return primera.imagen if primera else None


class ImagenProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='galeria')
    imagen = models.ImageField(upload_to='productos/galeria/')
    alt_text = models.CharField(max_length=150, blank=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Imagen de producto'
        verbose_name_plural = 'Imágenes de producto'
        ordering = ['orden']

    def __str__(self):
        return f'Imagen de {self.producto.nombre} ({self.orden})'


class EspecificacionProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='especificaciones')
    nombre = models.CharField(max_length=80, help_text='Ej. "Peso", "Cuello", "Norma"')
    valor = models.CharField(max_length=150, help_text='Ej. "28 g", "PCO 1881"')
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Especificación'
        verbose_name_plural = 'Especificaciones'
        ordering = ['orden']

    def __str__(self):
        return f'{self.nombre}: {self.valor}'


class Servicio(models.Model):
    nombre = models.CharField(max_length=150)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    descripcion_corta = models.CharField(max_length=220, blank=True)
    descripcion = models.TextField(blank=True)
    icono = models.CharField(
        max_length=60, blank=True, default='bi-gear',
        help_text='Nombre de clase de Bootstrap Icons, ej. "bi-droplet", "bi-shield-check"'
    )
    imagen = models.ImageField(upload_to='servicios/', blank=True, null=True)
    activo = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('catalogo:servicio_detalle', kwargs={'slug': self.slug})
