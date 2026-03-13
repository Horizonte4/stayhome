from django.contrib.auth import login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect

from properties.models import Property

from .forms import RegisterForm, EditProfileForm
from .models import Client, Owner

 #LAURA:
 # Aquí definimos las vistas para el home, login, registro, dashboard y edición de perfil.
 # La vista de home muestra las propiedades disponibles.???
 # La vista de login maneja la autenticación del usuario.
 # La vista de registro permite crear un nuevo usuario y asignarle un rol (cliente u owner).
 # La vista de dashboard muestra información relevante según el rol del usuario.
 # La vista de edición de perfil permite actualizar la información personal del usuario.
 
# HOME
def home(request):
    properties = Property.objects.available()
    return render(request, "users/home.html", {'properties': properties})

# LOGIN
def login_view(request):
    if request.method == 'GET':
        return render(request, 'registration/login.html', {
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
            return redirect('board')
        else:
            print("LOGIN FAILED")
            return render(request, 'registration/login.html', {
                'form': form,
                'error': 'Username and password do not match'
            })


# REGISTRO
def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()

            user_type = form.cleaned_data.get("user_type")

            if user_type == "client":
                Client.objects.create(user=user)

            elif user_type == "owner":
                Owner.objects.create(user=user)

            return redirect("login")

    else:
        form = RegisterForm()

    return render(request, "registration/signup.html", {"form": form})

# DASHBOARD
@login_required
def board(request):
    user = request.user

    if hasattr(user, 'owner'):
        role = "Owner"
        my_properties = Property.objects.filter(owner=user.owner)
    elif hasattr(user, 'client'):
        role = "Client"
        my_properties = Property.objects.none()
    else:
        role = "User"
        my_properties = Property.objects.none()

    return render(request, "users/board.html", {
        "role": role,
        "properties": my_properties,
    })

# LOGOUT
@login_required
def logout_view(request):
    if request.method == "POST":
        auth_logout(request)
        return redirect("home")

# EDIT PROFILE
@login_required
def edit_profile(request):

    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()
            return redirect('board')

    else:
        form = EditProfileForm(instance=request.user)

    return render(request, 'users/edit_profile.html', {'form': form})