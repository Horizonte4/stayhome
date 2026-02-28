from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario


class RegisterForm(UserCreationForm):

    TIPO_USUARIO = (
        ('cliente', 'Cliente'),
        ('propietario', 'Propietario'),
    )

    tipo_usuario = forms.ChoiceField(
        choices=TIPO_USUARIO,
        widget=forms.RadioSelect
    )

    class Meta:
        model = Usuario
        fields = (
            'email',
            'first_name',
            'last_name',
            'telefono',
            'password1',
            'password2',
        )
