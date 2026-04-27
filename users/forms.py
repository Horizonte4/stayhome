# Librerías externas
from django import forms
from django.contrib.auth.forms import UserCreationForm

# Archivos del proyecto
from .models import User


class RegisterForm(UserCreationForm):
    """Formulario de registro con selección de rol."""

    USER_TYPE = (
        ("client", "Client"),
        ("owner", "Owner"),
    )

    user_type = forms.ChoiceField(choices=USER_TYPE, widget=forms.RadioSelect)

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "phone",
            "password1",
            "password2",
        )


class EditProfileForm(forms.ModelForm):
    """Formulario para editar datos personales del usuario."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone"]
