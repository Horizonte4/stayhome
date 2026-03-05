from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    home,
    RegisterView,
    login_view,
    board,
    dashboard_client,
    dashboard_owner,
    logout_view
)

urlpatterns = [
    path('', home, name='home'),
    path('registration/', RegisterView.as_view(), name='registration'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/client/', dashboard_client, name='dashboard_client'),
    path('dashboard/owner/', dashboard_owner, name='dashboard_owner'),
    path('board/', board, name='board'),

    #path('profile/', ProfileView.as_view(), name='profile'),
]