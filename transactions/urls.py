from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    create_booking,
    owner_bookings,
    approve_booking,
    reject_booking,
    my_bookings,
    cancel_booking
)

app_name = 'transactions'

urlpatterns = [
    path("", my_bookings, name='my_bookings'),
    path("create/<int:property_id>/", create_booking, name="create_booking"),
    path("owner/", owner_bookings, name="owner_bookings"),
    path("<int:booking_id>/approve/", approve_booking, name="approve_booking"),
    path("<int:booking_id>/reject/", reject_booking, name="reject_booking"),
    path("<int:booking_id>/cancel/",cancel_booking, name="cancel_booking"),
    path('password-reset/',auth_views.PasswordResetView.as_view(
            template_name='auth/password_reset.html',
            email_template_name='registration/password_reset_email.html',
            success_url='/password-reset/done/'
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
            success_url='/reset/done/'
        ),
        name='password_reset_confirm'
    ),

    path('reset/done/',auth_views.PasswordResetCompleteView.as_view(
            template_name='auth/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
]