from django.urls import path
from django.urls import reverse_lazy
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
    path('password-reset/',auth_views.PasswordResetView.as_view(
        template_name='auth/password_reset.html',
        email_template_name='registration/password_reset_email.html'
        ),
        name='password_reset'
    ),

    path('password-reset/done/',auth_views.PasswordResetDoneView.as_view(
            template_name='auth/password_reset_done.html'
        ),
        name='password_reset_done'
    ),

    path('reset/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(
            template_name='auth/password_reset_confirm.html',
            success_url=reverse_lazy('password_reset_complete')
        ),
        name='password_reset_confirm'
    ),

    path('reset/done/',auth_views.PasswordResetCompleteView.as_view(
            template_name='auth/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
]