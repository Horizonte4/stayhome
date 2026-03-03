from django import forms
from .models import Propiedad


class PropiedadForm(forms.ModelForm):
    class Meta:
        model = Propiedad
        fields = [
            'titulo',
            'descripcion',
            'direccion',
            'ciudad',
            'precio',
            'estado',
            'tipo_publicacion',
            'habitaciones',
            'banos',
            'metros_cuadrados',
            'capacidad_personas',
            'imagen',
            'imagen_url',
            'publicacion_activa',
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Modern Downtown Apartment'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Describe highlights, amenities, nearby places...'}),
            'direccion': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '123 Main Street'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Downtown'}),
            'precio': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'step': '0.01'}),
            'estado': forms.Select(attrs={'class': 'form-input'}),
            'tipo_publicacion': forms.Select(attrs={'class': 'form-input'}),
            'habitaciones': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'banos': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'metros_cuadrados': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'step': 1}),
            'capacidad_personas': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-input'}),
            'imagen_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://...'}),
            'publicacion_activa': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['estado'].initial = 'disponible'
            self.fields['publicacion_activa'].initial = True

        # Mark core fields as required on the form level
        required_fields = [
            'titulo', 'descripcion', 'direccion', 'ciudad', 'precio', 'estado', 'tipo_publicacion',
            'habitaciones', 'banos', 'capacidad_personas'
        ]
        for name in required_fields:
            if name in self.fields:
                self.fields[name].required = True

    def clean(self):
        cleaned = super().clean()

        # Numeric validations
        for field in ['precio', 'habitaciones', 'banos', 'capacidad_personas']:
            value = cleaned.get(field)
            if value is not None and value <= 0:
                self.add_error(field, 'Debe ser mayor que cero.')

        metros = cleaned.get('metros_cuadrados')
        if metros is not None and metros < 0:
            self.add_error('metros_cuadrados', 'No puede ser negativo.')

        # Require at least one image source
        imagen = cleaned.get('imagen')
        imagen_url = cleaned.get('imagen_url')
        if not imagen and not imagen_url:
            self.add_error('imagen', 'Sube una imagen o proporciona una URL.')
            self.add_error('imagen_url', 'Sube una imagen o proporciona una URL.')

        return cleaned