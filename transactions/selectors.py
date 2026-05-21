from .models import Booking, Purchase


def get_client_bookings_context(user):
    """Obtiene las reservas y compras del cliente."""
    context = Booking.objects.client_context(user)
    context["purchased_properties"] = Purchase.objects.for_buyer(user)
    return context
