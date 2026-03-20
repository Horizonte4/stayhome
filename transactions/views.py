from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Booking
from .services import BookingService
from .mixins import BookingOwnerMixin
from .exceptions import PropertyPurchaseError
from .purchases import can_access_inactive_property, purchase_property
from properties.models import Property

@login_required
def create_booking(request, property_id):
    property = get_object_or_404(Property, id=property_id)

    if request.method == "POST":
        check_in = request.POST.get("check_in")
        check_out = request.POST.get("check_out")

        if not check_in or not check_out:
            messages.error(request, "Must select check in and check out.")
            return redirect("properties:property_detail", pk=property.id)

        if BookingService.has_conflict(property, check_in, check_out):
            messages.error(request, "These dates are already booked.")
            return redirect("properties:property_detail", pk=property.id)

        BookingService.create_booking(property, request.user, check_in, check_out)
        return redirect("transactions:my_bookings")


@login_required
def buy_property(request, property_id):
    property_obj = get_object_or_404(
        Property.objects.select_related("owner__user"),
        id=property_id,
    )

    if request.method != "POST":
        return redirect("properties:property_detail", pk=property_obj.pk)

    try:
        purchase_property(property_obj=property_obj, buyer=request.user)
    except PropertyPurchaseError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "Property purchased successfully.")

    if can_access_inactive_property(request.user, property_obj):
        return redirect("properties:property_detail", pk=property_obj.pk)

    return redirect("properties:list_properties")


@login_required
def my_bookings(request):
    context = BookingService.get_client_bookings(request.user)
    return render(request, "transactions/my_bookings.html", context)


@login_required
def owner_bookings(request):
    if not hasattr(request.user, "owner"):
        return redirect("board")
    context = BookingService.get_owner_bookings(request.user.owner)
    return render(request, "transactions/owner_bookings.html", context)


# OCP: una sola view maneja approve/reject/cancel
@login_required
def change_booking_status(request, booking_id, new_status):
    booking = get_object_or_404(Booking, id=booking_id)

    if not BookingOwnerMixin.is_booking_owner(request, booking):
        messages.error(request, "No tienes permiso para esta acción.")
        return redirect("transactions:owner_bookings")

    try:
        BookingService.change_status(booking, new_status)
    except ValueError:
        messages.error(request, "Estado inválido.")

    return redirect("transactions:owner_bookings")
