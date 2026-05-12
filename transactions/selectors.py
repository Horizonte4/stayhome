from .models import Booking, Purchase



def get_client_bookings_context(user):
    context = Booking.objects.client_context(user)
    context["purchased_properties"] = Purchase.objects.for_buyer(user)
    return context
