from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    home,
    RegistrarView,
    Inicio_SesionView,
    dashboard_cliente,
    dashboard_propietario,
)

urlpatterns = [
    path('', home, name='home'),
    path('registrar/', RegistrarView.as_view(), name='registrar'),
    path('inicio_sesion/', Inicio_SesionView.as_view(), name='inicio_sesion'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('dashboard/cliente/', dashboard_cliente, name='dashboard_cliente'),
    path('dashboard/propietario/', dashboard_propietario, name='dashboard_propietario'),
]