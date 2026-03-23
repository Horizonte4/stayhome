# Librerías externas
from django.urls import path

# Archivos del proyecto
from . import views

app_name = "transactions"

urlpatterns = [
    path("", views.my_bookings, name="my_bookings"),
    path("create/<int:property_id>/", views.create_booking, name="create_booking"),
    path(
        "purchase-request/<int:property_id>/",
        views.create_purchase_request,
        name="create_purchase_request"
    ),
    path("owner/", views.owner_bookings, name="owner_bookings"),
    path(
        "booking/<int:booking_id>/status/<str:new_status>/",
        views.change_booking_status,
        name="change_booking_status"
    ),
    path(
        "purchase-request/<int:request_id>/accept/",
        views.accept_purchase_request,
        name="accept_purchase_request"
    ),
    path(
        "purchase-request/<int:request_id>/reject/",
        views.reject_purchase_request,
        name="reject_purchase_request"
    ),
]