# transactions/services.py

from django.db.models import Q
from django.utils import timezone
from .models import Booking

class BookingService:
    """
    Responsabilidad única: lógica de negocio de reservas.
    Las views no deben saber cómo se aprueba o rechaza una reserva.
    """

    @staticmethod
    def has_conflict(property, check_in, check_out):
        return Booking.objects.filter(
            property=property,
            status="approved"
        ).filter(
            Q(check_in__lt=check_out) &
            Q(check_out__gt=check_in)
        ).exists()

    @staticmethod
    def create_booking(property, user, check_in, check_out):
        return Booking.objects.create(
            property=property,
            user=user,
            check_in=check_in,
            check_out=check_out,
            status="pending"
        )

    @staticmethod
    def change_status(booking, new_status):
        """
        OCP: abierto a nuevos estados sin modificar approve/reject por separado.
        """
        VALID_STATUSES = {"approved", "rejected", "cancelled"}
        if new_status not in VALID_STATUSES:
            raise ValueError(f"invalid status: {new_status}")
        booking.status = new_status
        booking.save()

    @staticmethod
    def get_client_bookings(user):
        today = timezone.now().date()
        bookings = Booking.objects.filter(user=user).select_related("property")
        return {
            "pending": bookings.filter(status="pending"),
            "approved": bookings.filter(status="approved", check_in__gte=today),
            "rejected": bookings.filter(status="rejected"),
        }

    @staticmethod
    def get_owner_bookings(owner):
        today = timezone.now().date()
        bookings = Booking.objects.filter(
            property__owner=owner
        ).select_related("property", "user")
        return {
            "pending": bookings.filter(status="pending"),
            "upcoming": bookings.filter(status="approved", check_out__gte=today),
            "rejected": bookings.filter(status="rejected"),
        }