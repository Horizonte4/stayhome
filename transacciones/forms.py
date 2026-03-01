from django import forms
from .models import SolicitudArriendo


class SolicitudArriendoForm(forms.ModelForm):
    class Meta:
        model = SolicitudArriendo
        fields = ['fecha_inicio_deseada', 'fecha_fin_deseada']
        widgets = {
            'fecha_inicio_deseada': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin_deseada': forms.DateInput(attrs={'type': 'date'}),
        }