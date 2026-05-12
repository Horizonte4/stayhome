from .models import Booking, Purchase

from django.conf import settings
from django.utils import timezone


def get_client_bookings_context(user):
    context = Booking.objects.client_context(user)
    context["purchased_properties"] = Purchase.objects.for_buyer(user)
    return context


@property
def can_cancel(self):
    today = timezone.localdate()
    cancel_days_limit = getattr(settings, "BOOKING_CANCEL_DAYS_LIMIT", 5)
    return (self.check_in - today).days > cancel_days_limit
