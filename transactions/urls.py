from django.urls import path
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
]