from django.shortcuts import render, redirect
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django import forms

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.db import IntegrityError

from .models import Usuario, Cliente, Propietario
from .forms import RegisterForm, LoginForm

def loginaccount(request):
    if request.method == 'GET':
        return render(request, 'login.html', {
            'form': AuthenticationForm()
        })
    else:
        form = AuthenticationForm(data=request.POST)

        print("FORM VALID:", form.is_valid())
        print("ERRORS:", form.errors)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            print("LOGIN SUCCESS")
            return redirect('tablero')
        else:
            print("LOGIN FAILED")
            return render(request, 'login.html', {
                'form': form,
                'error': 'Username and password do not match'
            })

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

@login_required
def dashboard(request):
    user = request.user

    if hasattr(user, 'propietario'):
        rol = "propietario"
    elif hasattr(user, 'cliente'):
        rol = "cliente"
    else:
        rol = "usuario"

    return render(request, "usuarios/tablero.html", {
        "rol": rol
    })

#@login_required

#def dashboard(request):
#   return render(request, "usuarios/dashboard.html")


def cerrar_sesion(request):
    logout(request)
    return redirect("inicio_sesion")

   