from django import forms
from .models import Cliente, SolicitudCotizacion


class SolicitudCotizacionForm(forms.ModelForm):
    nombre = forms.CharField(max_length=150, label='Nombre completo')
    empresa = forms.CharField(max_length=150, required=False, label='Empresa')
    correo = forms.EmailField(label='Correo electrónico')
    telefono = forms.CharField(max_length=30, required=False, label='Teléfono')
    ciudad = forms.CharField(max_length=100, required=False, label='Ciudad')

    # Honeypot anti-spam: campo oculto vía CSS que un humano nunca llena.
    sitio_web = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = SolicitudCotizacion
        fields = ['mensaje']
        widgets = {
            'mensaje': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Detalles adicionales de tu solicitud (opcional)'}),
        }
        labels = {'mensaje': 'Mensaje adicional'}

    def clean_sitio_web(self):
        valor = self.cleaned_data.get('sitio_web')
        if valor:
            raise forms.ValidationError('Envío inválido.')
        return valor

    def guardar_cliente(self):
        return Cliente.objects.create(
            nombre=self.cleaned_data['nombre'],
            empresa=self.cleaned_data.get('empresa', ''),
            correo=self.cleaned_data['correo'],
            telefono=self.cleaned_data.get('telefono', ''),
            ciudad=self.cleaned_data.get('ciudad', ''),
        )
