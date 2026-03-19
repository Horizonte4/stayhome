from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path("", views.my_bookings, name='my_bookings'),
    path("create/<int:property_id>/", views.create_booking, name="create_booking"),
    path("owner/", views.owner_bookings, name="owner_bookings"),
    path("booking/<int:booking_id>/status/<str:new_status>/",
         views.change_booking_status, name="change_booking_status")
]