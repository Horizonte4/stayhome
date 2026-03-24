from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.utils.translation import gettext_lazy as _

from properties.models import Property
from .exceptions import PropertyPurchaseError, PurchaseRequestError
from .mixins import BookingOwnerMixin
from .models import Booking, PurchaseRequest
from .selectors import can_access_inactive_property, get_owner_purchase_requests
from .services import BookingService, PurchaseRequestService


@login_required
def create_booking(request, property_id):
    """Crea una reserva para una propiedad si las fechas están disponibles."""
    property_obj = get_object_or_404(Property, id=property_id)

    if request.method != "POST":
        return redirect("properties:property_detail", pk=property_obj.id)

    check_in = request.POST.get("check_in")
    check_out = request.POST.get("check_out")

    if not check_in or not check_out:
        messages.error(request, "Must select check in and check out.")
        return redirect("properties:property_detail", pk=property_obj.id)

    if BookingService.has_conflict(property_obj, check_in, check_out):
        messages.error(request, "These dates are already booked.")
        return redirect("properties:property_detail", pk=property_obj.id)
    
    try:
        BookingService.create_booking(property_obj, request.user, check_in, check_out)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("properties:property_detail", pk=property_obj.id)

    return redirect("transactions:my_bookings")


@login_required
@require_POST
def create_purchase_request(request, property_id):
    """Envía una solicitud de compra al propietario de la propiedad."""
    property_obj = get_object_or_404(
        Property.objects.select_related("owner__user"),
        id=property_id,
    )

    try:
        PurchaseRequestService.create_request(property_obj=property_obj, buyer=request.user)
    except (PurchaseRequestError, PropertyPurchaseError) as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "Purchase request sent successfully.")

    if can_access_inactive_property(request.user, property_obj):
        return redirect("properties:property_detail", pk=property_obj.pk)

    return redirect("properties:list_properties")


@login_required
def my_bookings(request):
    """Muestra las reservas del cliente autenticado."""
    context = BookingService.get_client_bookings(request.user)
    return render(request, "transactions/my_bookings.html", context)


@login_required
def owner_bookings(request):
    """Muestra las reservas y solicitudes de compra del owner autenticado."""
    if not hasattr(request.user, "owner"):
        return redirect("board")
    context = BookingService.get_owner_bookings(request.user.owner)
    context["purchase_requests"] = get_owner_purchase_requests(request.user.owner)
    return render(request, "transactions/owner_bookings.html", context)


@login_required
def change_booking_status(request, booking_id, new_status):
    """Cambia el estado de una reserva (approve/reject/cancel)."""
    booking = get_object_or_404(Booking, id=booking_id)

    is_owner = BookingOwnerMixin.is_booking_owner(request, booking)
    is_client = booking.user == request.user and new_status == "cancelled"

    if not is_owner and not is_client:
        messages.error(request, "you are not allowed.")
        return redirect("transactions:my_bookings")

    try:
        BookingService.change_status(booking, new_status)
    except ValueError as e:
        messages.error(request, str(e))  # ← mensaje real del error

    if is_owner:
        return redirect("transactions:owner_bookings")

    return redirect("transactions:my_bookings")


@login_required
@require_POST
def accept_purchase_request(request, request_id):
    """Acepta una solicitud de compra pendiente."""
    purchase_request = get_object_or_404(
        PurchaseRequest.objects.select_related("property", "property__owner", "buyer"),
        id=request_id,
    )

    try:
        PurchaseRequestService.accept_request(purchase_request, request.user)
    except (PurchaseRequestError, PropertyPurchaseError) as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "Purchase request accepted successfully.")

    return redirect("transactions:owner_bookings")


@login_required
@require_POST
def reject_purchase_request(request, request_id):
    """Rechaza una solicitud de compra pendiente."""
    purchase_request = get_object_or_404(
        PurchaseRequest.objects.select_related("property", "property__owner", "buyer"),
        id=request_id,
    )

    try:
        PurchaseRequestService.reject_request(purchase_request, request.user)
    except (PurchaseRequestError, PropertyPurchaseError) as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "Purchase request rejected successfully.")

    return redirect("transactions:owner_bookings")