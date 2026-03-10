from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    home,
    register_view,
    login_view,
    board,
    edit_profile,
    logout_view
)

#LAURA:
# Aquí definimos las URLs para las vistas de usuarios.

urlpatterns = [
    path('', home, name='home'),
    path('registration/', register_view, name='registration'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('board/', board, name='board'),
    path('edit_profile/', edit_profile, name='edit_profile'),
]