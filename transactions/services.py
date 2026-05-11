from datetime import timedelta

from django.utils import timezone
from django.conf import settings
from .models import Booking, Purchase

from .selectors import get_client_bookings_context


class BookingService:
    @staticmethod
    def has_conflict(property_obj, check_in, check_out):
        return Booking.objects.filter(
            property=property_obj,
            status=Booking.STATUS_APPROVED,
            check_in__lt=check_out,
            check_out__gt=check_in,
        ).exists()

    @staticmethod
    def create_booking(property_obj, user, check_in, check_out):
        if property_obj.owner and property_obj.owner.user_id == user.id:
            raise ValueError("Owners cannot book their own properties.")

        if property_obj.listing_type == "sale":
            raise ValueError("Sale properties cannot receive bookings.")

        duration = (check_out - check_in).days
        if property_obj.listing_type == "long_term":
            if duration < 30:
                raise ValueError("Long term rentals require a minimum stay of 30 days.")
            if duration % 30 != 0:
                raise ValueError(
                    "Long term rentals must be booked in complete months (30, 60, 90 days...)."
                )

        if not property_obj.is_available(check_in, check_out):
            raise ValueError("The property is not available for those dates.")

        return Booking.objects.create(
            property=property_obj,
            user=user,
            check_in=check_in,
            check_out=check_out,
            status=Booking.STATUS_PENDING,
        )

    @staticmethod
    def change_status(booking, new_status):
        valid_statuses = {
            Booking.STATUS_APPROVED,
            Booking.STATUS_REJECTED,
            Booking.STATUS_CANCELLED,
        }

        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}")

        if new_status == Booking.STATUS_APPROVED:
            if BookingService.has_conflict(
                booking.property,
                booking.check_in,
                booking.check_out,
            ):
                raise ValueError("These dates are already booked.")

            booking.status = Booking.STATUS_APPROVED
            booking.save(update_fields=["status", "updated_at"])

            Booking.objects.filter(
                property=booking.property,
                status=Booking.STATUS_PENDING,
                check_in__lt=booking.check_out,
                check_out__gt=booking.check_in,
            ).exclude(pk=booking.pk).update(status=Booking.STATUS_REJECTED)
            return booking

        if new_status == Booking.STATUS_CANCELLED:
            today = timezone.localdate()
            cancel_days_limit = settings.BOOKING_CANCEL_DAYS_LIMIT
            limit_date = booking.check_in - timedelta(days=cancel_days_limit)
        if today > limit_date:
            raise ValueError(
                f"You can only cancel a booking at least {cancel_days_limit} days before check-in."
            )

        booking.status = new_status
        booking.save(update_fields=["status", "updated_at"])
        return booking

    @staticmethod
    def get_client_bookings(user):
        return get_client_bookings_context(user)

    @staticmethod
    def get_owner_bookings(owner):
        today = timezone.localdate()
        bookings = Booking.objects.filter(property__owner=owner).select_related(
            "property",
            "user",
        )
        return {
            "pending": bookings.filter(status=Booking.STATUS_PENDING),
            "upcoming": bookings.filter(
                status=Booking.STATUS_APPROVED,
                check_out__gte=today,
            ),
            "rejected": bookings.filter(status=Booking.STATUS_REJECTED),
            "past": bookings.filter(
                status=Booking.STATUS_APPROVED,
                check_out__lt=today,
            ),
        }


class PurchaseService:
    @staticmethod
    def request_purchase(property_obj, user):
        if property_obj.listing_type != "sale":
            raise ValueError("This property is not for sale.")

        if property_obj.owner and property_obj.owner.user_id == user.id:
            raise ValueError("You cannot buy your own property.")

        if Purchase.objects.filter(
            property=property_obj,
            status=Purchase.STATUS_APPROVED,
        ).exists():
            raise ValueError("This property has already been sold.")

        if Purchase.objects.filter(
            property=property_obj,
            buyer=user,
        ).exists():
            raise ValueError("You already have a purchase request for this property.")

        return Purchase.objects.create(
            property=property_obj,
            buyer=user,
            total_value=property_obj.price,
            status=Purchase.STATUS_PENDING,
        )

    @staticmethod
    def approve_purchase(purchase):
        if Purchase.objects.filter(
            property=purchase.property,
            status=Purchase.STATUS_APPROVED,
        ).exists():
            raise ValueError("This property has already been sold.")

        purchase.status = Purchase.STATUS_APPROVED
        purchase.save(update_fields=["status", "updated_at"])
        return purchase

    @staticmethod
    def reject_purchase(purchase):
        if purchase.status != Purchase.STATUS_PENDING:
            raise ValueError("Only pending purchases can be rejected.")

        purchase.status = Purchase.STATUS_REJECTED
        purchase.save(update_fields=["status", "updated_at"])
        return purchase
