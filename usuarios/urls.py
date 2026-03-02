from django.urls import path
from django.contrib.auth import views as auth_views
from .views import RegistrarView, dashboard, cerrar_sesion

urlpatterns = [
    path('registrar/', RegistrarView.as_view(), name='registrar'),
    path('inicio_sesion/', auth_views.LoginView.as_view(), name='inicio_sesion'),
    path('tablero/', dashboard, name='tablero'),
    path('logout/', cerrar_sesion, name='logout'),
    #path('profile/', ProfileView.as_view(), name='profile'),
]
