from django.shortcuts import render, redirect
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from properties.models import Property
from .forms import RegisterForm, EditProfileForm
from django.contrib.auth.forms import AuthenticationForm
from .models import Client, Owner
from django.contrib.auth import logout as auth_logout,login 


# HOME
def home(request):
    properties = Property.objects.available()
    return render(request, "users/home.html", {'properties': properties})


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
class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save()
        user_type = form.cleaned_data.get('user_type')

        if user_type == 'client':
            Client.objects.create(user=user)
        elif user_type == 'owner':
            Owner.objects.create(user=user)

        return super().form_valid(form)

@login_required
def board(request):
    user = request.user

    if hasattr(user, 'owner'):
        role = "Owner"
    elif hasattr(user, 'client'):
        role = "Client"
    else:
        role = "User"

    return render(request, "users/board.html", {
        "role": role
    })

#@login_required

#def dashboard(request):
#   return render(request, "usuarios/dashboard.html")

@login_required
def logout_view(request):
    if request.method == "POST":
        auth_logout(request)
        return redirect("home")

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
# DASHBOARDS (fuera de las clases)

@login_required
def dashboard_client(request):
    return render(request, "users/dashboard_client.html")


@login_required
def dashboard_owner(request):
    return render(request, "users/dashboard_owner.html")
