from datetime import timedelta

from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import Booking
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
            raise ValueError(_("Owners cannot book their own properties."))

        if property_obj.listing_type == "sale":
            raise ValueError(_("Sale properties cannot receive bookings."))

        if not property_obj.is_available(check_in, check_out):
            raise ValueError(_("The property is not available for those dates."))

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
            raise ValueError(_("Invalid status: %(status)s") % {"status": new_status})

        if new_status == Booking.STATUS_APPROVED:
            if BookingService.has_conflict(
                booking.property,
                booking.check_in,
                booking.check_out,
            ):
                raise ValueError(_("These dates are already booked."))

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
            limit_date = booking.check_in - timedelta(days=5)
            if today > limit_date:
                raise ValueError(
                    _(
                        "You can only cancel a booking at least 5 days before check-in."
                    )
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
