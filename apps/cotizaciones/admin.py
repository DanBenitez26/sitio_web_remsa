from django.contrib import admin
from .models import Cliente, SolicitudCotizacion, ItemCotizacion, Seguimiento


class SeguimientoInline(admin.TabularInline):
    model = Seguimiento
    extra = 0
    fields = ('tipo', 'fecha', 'nota', 'proximo_contacto', 'solicitud', 'creado_por')
    readonly_fields = ('creado_por',)
    ordering = ('-fecha',)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'empresa', 'correo', 'estado', 'responsable', 'ultimo_seguimiento', 'creado_en')
    list_filter = ('estado', 'responsable', 'creado_en')
    list_editable = ('estado',)
    search_fields = ('nombre', 'empresa', 'correo', 'telefono')
    readonly_fields = ('creado_en',)
    inlines = [SeguimientoInline]

    @admin.display(description='Último seguimiento')
    def ultimo_seguimiento(self, obj):
        seguimiento = obj.seguimientos.order_by('-fecha').first()
        return seguimiento.fecha if seguimiento else 'Sin seguimiento'

    def save_formset(self, request, form, formset, change):
        seguimientos = formset.save(commit=False)
        for seguimiento in seguimientos:
            if not seguimiento.creado_por:
                seguimiento.creado_por = request.user
            seguimiento.save()
        formset.save_m2m()


@admin.register(Seguimiento)
class SeguimientoAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'tipo', 'fecha', 'proximo_contacto', 'creado_por')
    list_filter = ('tipo', 'fecha', 'proximo_contacto')
    search_fields = ('cliente__nombre', 'cliente__empresa', 'cliente__correo', 'nota')
    readonly_fields = ('creado_en',)
    date_hierarchy = 'fecha'

    def save_model(self, request, obj, form, change):
        if not obj.creado_por:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)


class ItemCotizacionInline(admin.TabularInline):
    model = ItemCotizacion
    extra = 0
    readonly_fields = ('producto', 'cantidad', 'notas')
    can_delete = False


@admin.register(SolicitudCotizacion)
class SolicitudCotizacionAdmin(admin.ModelAdmin):
    list_display = ('folio', 'cliente', 'estado', 'creado_en')
    list_filter = ('estado', 'creado_en')
    search_fields = ('folio', 'cliente__nombre', 'cliente__empresa', 'cliente__correo')
    readonly_fields = ('folio', 'ip_origen', 'creado_en', 'actualizado_en')
    inlines = [ItemCotizacionInline]
    date_hierarchy = 'creado_en'
