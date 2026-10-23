from django.contrib import admin
from .models import Banner, Testimonio


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'orden', 'activo')
    list_editable = ('orden', 'activo')


@admin.register(Testimonio)
class TestimonioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'empresa', 'calificacion', 'orden', 'activo')
    list_editable = ('orden', 'activo')
