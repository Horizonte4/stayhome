# Librerías externas
from django.contrib.auth import login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect

# Archivos del proyecto
from properties.models import Property
from .forms import RegisterForm, EditProfileForm
from .models import Client, Owner


def login_view(request):
    form = AuthenticationForm(data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        next_url = request.GET.get("next") or request.POST.get("next")
        return redirect(next_url or "home")
    return render(request, "registration/login.html", {"form": form})


def register_view(request):
    """Crea un nuevo usuario y le asigna rol de cliente u owner."""
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        user_type = form.cleaned_data.get("user_type")
        if user_type == "client":
            Client.objects.create(user=user)
        elif user_type == "owner":
            Owner.objects.create(user=user)
        return redirect("login")
    return render(request, "registration/signup.html", {"form": form})


@login_required
def board(request):
    """Muestra el dashboard según el rol del usuario."""
    user = request.user
    role = user.role  # usa el mixin que ya definimos en el modelo

    my_properties = (
        Property.objects.filter(owner=user.owner)
        if role == "owner"
        else Property.objects.none()
    )

    return render(request, "users/board.html", {
        "role": role,
        "properties": my_properties,
    })


@login_required
def logout_view(request):
    """Cierra la sesión del usuario."""
    if request.method == "POST":
        auth_logout(request)
    return redirect("home")


@login_required
def edit_profile(request):
    """Permite al usuario editar su información personal."""
    form = EditProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("board")
    return render(request, "users/edit_profile.html", {"form": form})