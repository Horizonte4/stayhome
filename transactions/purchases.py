from django.db import transaction

from .exceptions import (
    OwnerCannotBuyOwnPropertyError,
    PropertyAlreadyPurchasedError,
    PropertyNotPurchasableError,
)
from .models import Contract


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


@transaction.atomic
def purchase_property(*, property_obj, buyer):
    if property_obj.listing_type != "sale":
        raise PropertyNotPurchasableError("This property is not available for sale.")

    if not property_obj.active_listing:
        raise PropertyAlreadyPurchasedError("This property has already been purchased.")

    if property_obj.state != "available":
        raise PropertyNotPurchasableError("This property is not currently available for purchase.")

    if not property_obj.owner:
        raise PropertyNotPurchasableError("This property has no owner assigned.")

    if property_obj.owner.user_id == buyer.id:
        raise OwnerCannotBuyOwnPropertyError("You cannot buy your own property.")

    if has_sale_contract(property_obj):
        raise PropertyAlreadyPurchasedError("This property has already been purchased.")

    contract = Contract.objects.create(
        property=property_obj,
        tenant=buyer,
        type="sale",
        status="completed",
        total_value=property_obj.price,
    )

    property_obj.active_listing = False
    property_obj.save(update_fields=["active_listing"])

    return contract
