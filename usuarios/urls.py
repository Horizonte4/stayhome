from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    home,
    RegistrarView,
    Inicio_SesionView,
    tablero,
    dashboard_cliente,
    dashboard_propietario,
)
from .views import RegistrarView
urlpatterns = [
    path('', home, name='home'),
    path('registrar/', RegistrarView.as_view(), name='registrar'),
    path('inicio_sesion/', Inicio_SesionView, name='inicio_sesion'),
    path('logout/', auth_views.LogoutView.as_view, name='logout'),
    path('dashboard/cliente/', dashboard_cliente, name='dashboard_cliente'),
    path('dashboard/propietario/', dashboard_propietario, name='dashboard_propietario'),
    path('tablero/', tablero, name='tablero'),

    #path('profile/', ProfileView.as_view(), name='profile'),
]