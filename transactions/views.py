from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Booking
from properties.models import Property
from django.shortcuts import render
from django.utils import timezone
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseForbidden
from django.db.models import Q



#CREATE BOOKING
@login_required
def create_booking(request, property_id):
    property = get_object_or_404(Property, id=property_id)
    
    if request.method == "POST":
        check_in = request.POST.get("check_in")
        check_out = request.POST.get("check_out")
        if not check_in or not check_out:
            messages.error(request, "Must select chech in and check out.")
            return redirect("properties:property_detail", pk=property.id)
        
         # VERIFICAR CONFLICTO
        conflict = Booking.objects.filter(
            property=property,
            status="approved"
        ).filter(
            Q(check_in__lt=check_out) &
            Q(check_out__gt=check_in)
        ).exists()

        if conflict:
            messages.error(request, "These dates are already booked.")
            return redirect("properties:property_detail", pk=property.id)


        Booking.objects.create(
            property=property,
            user=request.user,
            check_in=check_in,
            check_out=check_out,
            status="pending"
        )
        
        return redirect("transactions:my_bookings")

#CLIENT BOOKIGS
@login_required
def my_bookings(request):

    bookings = Booking.objects.filter(user=request.user).select_related("property")

    pending = bookings.filter(status="pending")
    approved = bookings.filter(status="approved", check_in__gte=timezone.now().date())
    rejected = bookings.filter(status="rejected")
    cancelled = bookings.filter(check_out__lt=timezone.now().date())
    print(bookings.values("status"))
    context = {
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "cancelled": cancelled
    }

    return render(request, "transactions/my_bookings.html", context)

#OWNER BOOKINGS
@login_required
def owner_bookings(request):

    if not hasattr(request.user, "owner"):
        return redirect("board")

    bookings = Booking.objects.filter(
        property__owner=request.user.owner
    ).select_related("property", "user")

@login_required
def owner_bookings(request):

    owner = request.user.owner

    bookings = Booking.objects.filter(
        property__owner=owner
    ).select_related("property", "user")

    pending = bookings.filter(status="pending")

    upcoming = bookings.filter(
        status="approved",
        check_out__gte=timezone.now().date()
    )

    rejected = bookings.filter(status="rejected")
    
    cancelled = bookings.filter(status="cancelled")
    
    
    past = bookings.filter(
        status="approved",
        check_out__lt=timezone.now().date()
    )

    context = {
        "pending": pending,
        "upcoming": upcoming,
        "rejected": rejected,
        "past": past,
        "canccelled": cancelled
    }

    return render(request, "transactions/owner_bookings.html", context)


@login_required
def approve_booking(request, booking_id):

    booking = get_object_or_404(Booking, id=booking_id)

    # seguridad: solo el owner puede aprobar
    if booking.property.owner == request.user.owner:
        booking.status = "approved"
        booking.save()

    return redirect("transactions:owner_bookings")

@login_required
def reject_booking(request, booking_id):

    booking = get_object_or_404(Booking, id=booking_id)

    if booking.property.owner == request.user.owner:
        booking.status = "rejected"
        booking.save()

    return redirect("transactions:owner_bookings")

@login_required
def cancel_booking(request, booking_id):

    booking = get_object_or_404(Booking, id=booking_id)

    if booking.property.owner == request.user.owner:
        booking.status = "cancelled"
        booking.save()

    return redirect("transactions:owner_bookings")
