from django import forms
from .models import Propiedad

class PropiedadForm(forms.ModelForm):
    # Definir opciones para el campo "estado"
    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('ocupado', 'Ocupado'),
        # Puedes agregar más estados si es necesario
    ]

    class Meta:
        model = Propiedad
        fields = ['titulo', 'ciudad', 'precio', 'estado', 'publicacion_activa']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-input'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-input'}),
            'precio': forms.NumberInput(attrs={'class': 'form-input'}),
            
            # Cambiar publicacion_activa para usar CheckboxInput
            'publicacion_activa': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def __init__(self, *args, **kwargs):
        super(PropiedadForm, self).__init__(*args, **kwargs)
        # Establecer valores predeterminados si es necesario
        if not self.instance.pk:  # Si estamos creando una nueva propiedad
            self.fields['estado'].initial = 'disponible'  # Valor predeterminado para 'estado'
            self.fields['publicacion_activa'].initial = True  # Valor predeterminado para 'publicacion_activa'