from .models import Booking, Contract


def has_sale_contract(property_obj, buyer=None):
    return property_obj.has_sale_contract(buyer=buyer)


def can_access_property(user, property_obj):
    return property_obj.can_be_accessed_by(user)


def get_client_bookings_context(user):
    context = Booking.objects.client_context(user)
    context["purchased_contracts"] = Contract.objects.purchased_by(user)
    return context