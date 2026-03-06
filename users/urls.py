from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    home,
    RegisterView,
    login_view,
    board,
    edit_profile,
    logout_view
)

urlpatterns = [
    path('', home, name='home'),
    path('registration/', RegisterView.as_view(), name='registration'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('board/', board, name='board'),
    path('edit_profile/', edit_profile, name='edit_profile'),


    #path('dashboard/client/', dashboard_client, name='dashboard_client'),
    #path('dashboard/owner/', dashboard_owner, name='dashboard_owner'),
    

    #path('profile/', ProfileView.as_view(), name='profile'),
]