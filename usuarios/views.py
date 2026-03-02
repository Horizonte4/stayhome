from django.shortcuts import render
from django.shortcuts import render, redirect
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from propiedades.models import Propiedad
from .forms import RegisterForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from .models import Cliente, Propietario


# HOME
def home(request):
    propiedades = Propiedad.objects.disponibles()
    return render(request, "usuarios/home.html", {'propiedades': propiedades})


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


# REGISTRO
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
def tablero(request):
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

# DASHBOARDS (fuera de las clases)
@login_required
def dashboard_cliente(request):
    return render(request, "usuarios/dashboard_cliente.html")


@login_required
def dashboard_propietario(request):
    return render(request, "usuarios/dashboard_propietario.html")
   