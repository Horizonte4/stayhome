from django.shortcuts import render, redirect
from .models import Usuario
from django import forms
from django.views.generic import CreateView
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy

from django.contrib.auth.views import LoginView
from .forms import RegisterForm
from .models import Cliente, Propietario


class Inicio_SesionView(LoginView):
    template_name = 'registration/login.html'

    def get_success_url(self):
        user = self.request.user

        if hasattr(user, 'propietario'):
            return reverse_lazy('dashboard_propietario')

        if hasattr(user, 'cliente'):
            return reverse_lazy('dashboard_cliente')

        return reverse_lazy('home')

class RegistrarView(CreateView):
    form_class = RegisterForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('inicio_sesion')

    def form_valid(self, form):
        user = form.save()

        tipo = form.cleaned_data.get('tipo_usuario')

        if tipo == 'cliente':
            Cliente.objects.create(usuario=user)
        elif tipo == 'propietario':
            Propietario.objects.create(usuario=user)

        return super().form_valid(form)


   