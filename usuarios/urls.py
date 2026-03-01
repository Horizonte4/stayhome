from django.urls import path
from .views import (
    RegistrarView,
    Inicio_SesionView,
    home,
    dashboard_cliente,
    dashboard_propietario,
)

urlpatterns = [
    path('', home, name='home'),
    path('registrar/', RegistrarView.as_view(), name='registrar'),
    path('inicio_sesion/', Inicio_SesionView.as_view(), name='inicio_sesion'),
    path('dashboard_cliente/', dashboard_cliente, name='dashboard_cliente'),
    path('dashboard_propietario/', dashboard_propietario, name='dashboard_propietario'),
]