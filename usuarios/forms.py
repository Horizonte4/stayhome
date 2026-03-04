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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ['email', 'first_name', 'last_name', 'telefono', 'password1', 'password2', 'tipo_usuario']:
            if name in self.fields:
                self.fields[name].required = True
                self.fields[name].widget.attrs.setdefault('required', 'required')

    def clean(self):
        cleaned = super().clean()
        # Ensure telefono present
        telefono = cleaned.get('telefono')
        if not telefono:
            self.add_error('telefono', 'El teléfono es obligatorio.')
        return cleaned
        
class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise forms.ValidationError("Email o contraseña incorrectos.")

        return cleaned_data
