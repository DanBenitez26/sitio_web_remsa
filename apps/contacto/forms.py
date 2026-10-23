from django import forms
import re
import unicodedata
from .models import MensajeContacto


class ContactoForm(forms.ModelForm):
    sitio_web = forms.CharField(required=False, widget=forms.HiddenInput())  # honeypot

    class Meta:
        model = MensajeContacto
        fields = ['nombre', 'correo', 'telefono', 'asunto', 'mensaje']
        widgets = {
            'mensaje': forms.Textarea(attrs={'rows': 5}),
        }

    def clean_sitio_web(self):
        valor = self.cleaned_data.get('sitio_web')
        if valor:
            raise forms.ValidationError('Envío inválido.')
        return valor


class ChatbotLeadForm(forms.Form):
    nombre = forms.CharField(max_length=150, min_length=2)
    empresa = forms.CharField(max_length=150, min_length=2)
    telefono = forms.CharField(max_length=30)
    correo = forms.EmailField(max_length=254)
    producto = forms.CharField(max_length=150, required=False)
    mensaje = forms.CharField(max_length=2000, required=False)
    sitio_web = forms.CharField(required=False)
    submission_id = forms.UUIDField(widget=forms.HiddenInput())

    def clean_nombre(self):
        return self._clean_text("nombre")

    def clean_empresa(self):
        return self._clean_text("empresa")

    def clean_correo(self):
        return self._clean_text("correo")

    def clean_telefono(self):
        telefono = self._clean_text("telefono")
        digits = re.sub(r"\D", "", telefono)
        if not 10 <= len(digits) <= 15:
            raise forms.ValidationError(
                "Ingresa un teléfono válido de 10 a 15 dígitos."
            )
        return telefono

    def clean_producto(self):
        return self._clean_text("producto")

    def clean_mensaje(self):
        return self._clean_text("mensaje")

    def clean_sitio_web(self):
        if self.cleaned_data.get("sitio_web"):
            raise forms.ValidationError("No se pudo procesar la solicitud.")
        return ""

    def _clean_text(self, field_name):
        value = self.cleaned_data[field_name]
        value = unicodedata.normalize("NFC", value)
        return " ".join(value.split())


class ContactoCentroamericaForm(forms.Form):
    nombre = forms.CharField(max_length=150, min_length=2)
    empresa = forms.CharField(max_length=150, min_length=2)
    correo = forms.EmailField(max_length=254)
    telefono = forms.CharField(max_length=30)
    asunto = forms.CharField(max_length=150, min_length=3)
    mensaje = forms.CharField(max_length=2000, min_length=10)
    acepta_privacidad = forms.BooleanField(required=True)
    sitio_web = forms.CharField(required=False)  # honeypot

    def _limpio(self, campo):
        valor = unicodedata.normalize('NFC', self.cleaned_data[campo])
        return ' '.join(valor.split())

    def clean_nombre(self):
        return self._limpio('nombre')

    def clean_empresa(self):
        return self._limpio('empresa')

    def clean_asunto(self):
        return self._limpio('asunto')

    def clean_correo(self):
        return self._limpio('correo')

    def clean_telefono(self):
        telefono = self._limpio('telefono')
        digits = re.sub(r'\D', '', telefono)
        if not 8 <= len(digits) <= 15 or not re.fullmatch(r'[\d\s+()\-.]+', telefono):
            raise forms.ValidationError('Ingresa un teléfono válido de 8 a 15 dígitos.')
        return telefono

    def clean_mensaje(self):
        return unicodedata.normalize('NFC', self.cleaned_data['mensaje']).strip()

    def clean_sitio_web(self):
        if self.cleaned_data.get('sitio_web'):
            raise forms.ValidationError('No se pudo procesar la solicitud.')
        return ''


class SolicitudCatalogoForm(forms.Form):
    nombre = forms.CharField(max_length=150)
    empresa = forms.CharField(max_length=150)
    correo = forms.EmailField(max_length=254)
    telefono = forms.CharField(max_length=30)
    producto = forms.CharField(max_length=150)
    mensaje = forms.CharField(max_length=2000, required=False)
    pagina = forms.CharField(max_length=500, required=False)
    acepta_privacidad = forms.BooleanField(required=True)
    sitio_web = forms.CharField(required=False)

    def clean_telefono(self):
        telefono = self.cleaned_data['telefono'].strip()
        digits = re.sub(r'\D', '', telefono)
        if not 10 <= len(digits) <= 15:
            raise forms.ValidationError('Ingresa un teléfono válido de 10 a 15 dígitos.')
        return telefono

    def clean_sitio_web(self):
        if self.cleaned_data.get('sitio_web'):
            raise forms.ValidationError('No se pudo procesar la solicitud.')
        return ''

    def clean_pagina(self):
        pagina = self.cleaned_data.get('pagina', '').strip()
        if not pagina:
            return '/catalogo/'
        if (
            not pagina.startswith('/')
            or pagina.startswith('//')
            or '\r' in pagina
            or '\n' in pagina
        ):
            raise forms.ValidationError('La página de origen no es válida.')
        return pagina
