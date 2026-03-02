from django.shortcuts import render, redirect
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from propiedades.models import Propiedad
from .forms import RegisterForm
from .models import Cliente, Propietario


def home(request):
    propiedades = Propiedad.objects.disponibles()
    return render(request, "usuarios/home.html", {'propiedades': propiedades})


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
        self.object = form.save()
        tipo = form.cleaned_data.get('tipo_usuario')

        if tipo == 'cliente':
            Cliente.objects.create(usuario=self.object)
        elif tipo == 'propietario':
            Propietario.objects.create(usuario=self.object)

        return redirect(self.get_success_url())


@login_required
def dashboard_cliente(request):
    return render(request, "usuarios/dashboard_cliente.html")


@login_required
def dashboard_propietario(request):
    return render(request, "usuarios/dashboard_propietario.html")