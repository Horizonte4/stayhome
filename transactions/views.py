from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from properties.models import Property

from .mixins import BookingOwnerMixin
from .models import Booking, Purchase
from .services import BookingService, PurchaseService


@login_required
def create_booking(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)

    if request.method != "POST":
        return redirect("properties:property_detail", pk=property_obj.id)

    check_in = request.POST.get("check_in")
    check_out = request.POST.get("check_out")

    if not check_in or not check_out:
        messages.error(request, "Must select check in and check out.")
        return redirect("properties:property_detail", pk=property_obj.id)

    try:
        check_in_date = datetime.strptime(check_in, "%Y-%m-%d").date()
        check_out_date = datetime.strptime(check_out, "%Y-%m-%d").date()
    except ValueError:
        messages.error(request, "Dates must use the YYYY-MM-DD format.")
        return redirect("properties:property_detail", pk=property_obj.id)

    if check_in_date >= check_out_date:
        messages.error(request, "Check-out must be later than check-in.")
        return redirect("properties:property_detail", pk=property_obj.id)

    if BookingService.has_conflict(property_obj, check_in_date, check_out_date):
        messages.error(request, "These dates are already booked.")
        return redirect("properties:property_detail", pk=property_obj.id)

    try:
        BookingService.create_booking(
            property_obj,
            request.user,
            check_in_date,
            check_out_date,
        )
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("properties:property_detail", pk=property_obj.id)

    return redirect("transactions:my_bookings")


@login_required
def my_bookings(request):
    context = BookingService.get_client_bookings(request.user)
    return render(request, "transactions/my_bookings.html", context)


@login_required
def owner_bookings(request):
    if not hasattr(request.user, "owner"):
        return redirect("board")
    context = BookingService.get_owner_bookings(request.user.owner)
    context["purchases"] = Purchase.objects.for_owner(request.user.owner).filter(
        status=Purchase.STATUS_PENDING
    )
    context["completed_purchases"] = Purchase.objects.for_owner(
        request.user.owner
    ).exclude(status=Purchase.STATUS_PENDING)
    return render(request, "transactions/owner_bookings.html", context)


@login_required
def change_booking_status(request, booking_id, new_status):
    booking = get_object_or_404(Booking, id=booking_id)
    is_owner = BookingOwnerMixin.is_booking_owner(request, booking)
    is_client = booking.user == request.user and new_status == Booking.STATUS_CANCELLED

    if not is_owner and not is_client:
        messages.error(request, "You are not allowed to change this booking.")
        return redirect("transactions:my_bookings")

    try:
        BookingService.change_status(booking, new_status)
    except ValueError as exc:
        messages.error(request, str(exc))
        if is_owner:
            return redirect("transactions:owner_bookings")
        return redirect("transactions:my_bookings")

    if is_owner:
        return redirect("transactions:owner_bookings")
    return redirect("transactions:my_bookings")


@login_required
def request_purchase(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)

    if request.method != "POST":
        return redirect("properties:property_detail", pk=property_obj.id)

    try:
        PurchaseService.request_purchase(property_obj, request.user)
        messages.success(request, "Purchase request sent successfully.")
    except ValueError as exc:
        messages.error(request, str(exc))

    return redirect("properties:property_detail", pk=property_obj.id)


@login_required
def change_purchase_status(request, purchase_id, new_status):
    purchase = get_object_or_404(Purchase, id=purchase_id)

    if purchase.property.owner.user != request.user:
        messages.error(request, "You are not allowed to change this purchase.")
        return redirect("transactions:owner_bookings")

    try:
        if new_status == Purchase.STATUS_APPROVED:
            PurchaseService.approve_purchase(purchase)
        elif new_status == Purchase.STATUS_REJECTED:
            PurchaseService.reject_purchase(purchase)
        else:
            raise ValueError(f"Invalid status: {new_status}")
    except ValueError as exc:
        messages.error(request, str(exc))

    return redirect("transactions:owner_bookings")


@login_required
def cancel_booking(request, booking_id):
    if request.method != "POST":
        return redirect("transactions:my_bookings")

    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    try:
        BookingService.change_status(booking, Booking.STATUS_CANCELLED)
        messages.success(request, "Booking cancelled successfully.")
    except ValueError as exc:
        messages.error(request, str(exc))

    return redirect("transactions:my_bookings")
