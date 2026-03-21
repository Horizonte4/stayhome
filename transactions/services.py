# transactions/services.py

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from .exceptions import (
    DuplicatePurchaseRequestError,
    OwnerCannotBuyOwnPropertyError,
    PropertyAlreadyPurchasedError,
    PropertyNotPurchasableError,
    PurchaseRequestError,
    PurchaseRequestPermissionError,
)
from .models import Booking, Contract, PurchaseRequest
from .selectors import get_client_bookings_context, has_sale_contract

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
        return get_client_bookings_context(user)

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


class PurchaseRequestService:
    @staticmethod
    def _validate_purchasable_property(property_obj):
        if property_obj.listing_type != "sale":
            raise PropertyNotPurchasableError("This property is not available for sale.")

        if not property_obj.active_listing:
            raise PropertyAlreadyPurchasedError("This property is no longer available.")

        if property_obj.state != "available":
            raise PropertyNotPurchasableError("This property is not currently available for purchase.")

        if not property_obj.owner:
            raise PropertyNotPurchasableError("This property has no owner assigned.")

        if has_sale_contract(property_obj):
            raise PropertyAlreadyPurchasedError("This property has already been sold.")

    @staticmethod
    def create_request(property_obj, buyer):
        PurchaseRequestService._validate_purchasable_property(property_obj)

        if property_obj.owner.user_id == buyer.id:
            raise OwnerCannotBuyOwnPropertyError("You cannot request the purchase of your own property.")

        purchase_request, created = PurchaseRequest.objects.get_or_create(
            property=property_obj,
            buyer=buyer,
            defaults={"status": PurchaseRequest.STATUS_PENDING},
        )

        if not created and purchase_request.status == PurchaseRequest.STATUS_PENDING:
            raise DuplicatePurchaseRequestError("You already have a pending purchase request for this property.")

        if not created:
            purchase_request.status = PurchaseRequest.STATUS_PENDING
            purchase_request.save(update_fields=["status", "updated_at"])

        return purchase_request

    @staticmethod
    def _ensure_owner_permission(purchase_request, acting_user):
        owner_user_id = getattr(purchase_request.property.owner, "user_id", None)
        if owner_user_id != acting_user.id:
            raise PurchaseRequestPermissionError("Only the owner can update this purchase request.")

    @staticmethod
    @transaction.atomic
    def accept_request(purchase_request, acting_user):
        PurchaseRequestService._ensure_owner_permission(purchase_request, acting_user)
        PurchaseRequestService._validate_purchasable_property(purchase_request.property)

        if purchase_request.status != PurchaseRequest.STATUS_PENDING:
            raise PurchaseRequestError("Only pending purchase requests can be accepted.")

        purchase_request.status = PurchaseRequest.STATUS_ACCEPTED
        purchase_request.save(update_fields=["status", "updated_at"])

        Contract.objects.create(
            property=purchase_request.property,
            tenant=purchase_request.buyer,
            type="sale",
            status="completed",
            total_value=purchase_request.property.price,
        )

        purchase_request.property.active_listing = False
        purchase_request.property.save(update_fields=["active_listing"])

        PurchaseRequest.objects.filter(
            property=purchase_request.property,
            status=PurchaseRequest.STATUS_PENDING,
        ).exclude(pk=purchase_request.pk).update(
            status=PurchaseRequest.STATUS_REJECTED
        )

        return purchase_request

    @staticmethod
    def reject_request(purchase_request, acting_user):
        PurchaseRequestService._ensure_owner_permission(purchase_request, acting_user)

        if purchase_request.status != PurchaseRequest.STATUS_PENDING:
            raise PurchaseRequestError("Only pending purchase requests can be rejected.")

        purchase_request.status = PurchaseRequest.STATUS_REJECTED
        purchase_request.save(update_fields=["status", "updated_at"])
        return purchase_request
