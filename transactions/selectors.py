from django.utils import timezone

from .models import Booking, Contract


def has_sale_contract(property_obj, buyer=None):
    contracts = Contract.objects.filter(property=property_obj, type=Contract.TYPE_SALE)
    if buyer is not None:
        contracts = contracts.filter(tenant=buyer)
    return contracts.exists()


def can_access_property(user, property_obj):
    if not has_sale_contract(property_obj):
        return True

    if not getattr(user, "is_authenticated", False):
        return False

    if property_obj.owner and property_obj.owner.user_id == user.id:
        return True

    return has_sale_contract(property_obj, buyer=user)


def get_client_bookings_context(user):
    today = timezone.localdate()
    bookings = Booking.objects.filter(user=user).select_related(
        "property",
        "property__owner",
        "property__owner__user",
    )
    purchased_contracts = (
        Contract.objects.filter(tenant=user, type=Contract.TYPE_SALE)
        .select_related("property", "property__owner", "property__owner__user")
        .order_by("-created_at")
    )

    return {
        "pending": bookings.filter(status=Booking.STATUS_PENDING),
        "approved": bookings.filter(
            status=Booking.STATUS_APPROVED,
            check_in__gte=today,
        ),
        "rejected": bookings.filter(status=Booking.STATUS_REJECTED),
        "cancelled": bookings.filter(status=Booking.STATUS_CANCELLED),
        "purchased_contracts": purchased_contracts,
    }
