from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from .models import User


class RegisterForm(UserCreationForm):

    USER_TYPE = (
        ('client', 'Client'),
        ('owner', 'Owner'),
    )

    user_type = forms.ChoiceField(
        choices=USER_TYPE,
        widget=forms.RadioSelect
    )

    class Meta:
        model = User
        fields = (
            'email',
            'first_name',
            'last_name',
            'phone',
            'password1',
            'password2',
        )
        
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
