from django.utils import timezone

from .models import Booking, Contract, PurchaseRequest


def has_sale_contract(property_obj, buyer=None):
    contracts = Contract.objects.filter(property=property_obj, type="sale")
    if buyer is not None:
        contracts = contracts.filter(tenant=buyer)
    return contracts.exists()


def can_access_inactive_property(user, property_obj):
    if property_obj.active_listing:
        return True

    if not getattr(user, "is_authenticated", False):
        return False

    if property_obj.owner and property_obj.owner.user_id == user.id:
        return True

    return has_sale_contract(property_obj, buyer=user)


def can_contact_owner_for_property(user, property_obj):
    if not getattr(user, "is_authenticated", False):
        return False

    if not property_obj.owner or property_obj.owner.user_id == user.id:
        return False

    return has_sale_contract(property_obj, buyer=user)


def get_purchase_request_for_user(property_obj, user):
    if not getattr(user, "is_authenticated", False):
        return None

    return (
        PurchaseRequest.objects.filter(property=property_obj, buyer=user)
        .order_by("-created_at")
        .first()
    )


def get_client_bookings_context(user):
    today = timezone.now().date()
    bookings = Booking.objects.filter(user=user).select_related(
        "property",
        "property__owner",
        "property__owner__user",
    )
    purchased_contracts = (
        Contract.objects.filter(tenant=user, type="sale")
        .select_related("property", "property__owner", "property__owner__user")
        .order_by("-created_at")
    )

    return {
        "pending": bookings.filter(status="pending"),
        "approved": bookings.filter(status="approved", check_in__gte=today),
        "rejected": bookings.filter(status="rejected"),
        "cancelled": bookings.filter(status="cancelled"),
        "purchased_contracts": purchased_contracts,
    }


def get_owner_purchase_requests(owner):
    return (
        PurchaseRequest.objects.filter(property__owner=owner)
        .select_related("property", "property__owner", "property__owner__user", "buyer")
        .order_by("-created_at")
    )
