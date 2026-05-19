from datetime import timedelta

from django.db import transaction
from django.utils.translation import gettext as _
from django.utils import timezone
from django.conf import settings
from notifications.services import NotificationService
from .models import Booking, Purchase
from .selectors import get_client_bookings_context


class BookingService:
    @staticmethod
    def has_conflict(property_obj, check_in, check_out):
        """Verifica si hay una reserva aprobada que choca con las fechas dadas."""
        return Booking.objects.filter(
            property=property_obj,
            status=Booking.STATUS_APPROVED,
            check_in__lt=check_out,
            check_out__gt=check_in,
        ).exists()

    @staticmethod
    def create_booking(property_obj, user, check_in, check_out):
        """Crea una reserva si el usuario, la propiedad y las fechas son válidos."""
        if property_obj.owner and property_obj.owner.user_id == user.id:
            raise ValueError(_("Owners cannot book their own properties."))

        if property_obj.listing_type == "sale":
            raise ValueError(_("Sale properties cannot receive bookings."))

        duration = (check_out - check_in).days
        if property_obj.listing_type == "long_term":
            if duration < 30:
                raise ValueError(
                    _("Long term rentals require a minimum stay of 30 days.")
                )
            if duration % 30 != 0:
                raise ValueError(
                    _(
                        "Long term rentals must be booked in complete months (30, 60, 90 days...)."
                    )
                )

        if not property_obj.is_available(check_in, check_out):
            raise ValueError(_("The property is not available for those dates."))

        with transaction.atomic():
            booking = Booking.objects.create(
                property=property_obj,
                user=user,
                check_in=check_in,
                check_out=check_out,
                status=Booking.STATUS_PENDING,
            )
            NotificationService.send_booking_request_email(booking)
            return booking

    @staticmethod
    def change_status(booking, new_status):
        """Cambia el estado de una reserva y envía los correos correspondientes."""
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

            with transaction.atomic():
                booking.status = Booking.STATUS_APPROVED
                booking.save(update_fields=["status", "updated_at"])

                overlapping_bookings = list(
                    Booking.objects.filter(
                        property=booking.property,
                        status=Booking.STATUS_PENDING,
                        check_in__lt=booking.check_out,
                        check_out__gt=booking.check_in,
                    )
                    .exclude(pk=booking.pk)
                    .select_related("property", "user")
                )
                for overlapping_booking in overlapping_bookings:
                    overlapping_booking.status = Booking.STATUS_REJECTED
                    overlapping_booking.save(update_fields=["status", "updated_at"])

            try:
                NotificationService.send_booking_approved_email(booking)
            except ValueError:
                pass

            for overlapping_booking in overlapping_bookings:
                try:
                    NotificationService.send_booking_rejected_email(overlapping_booking)
                except ValueError:
                    pass
            return booking

        if new_status == Booking.STATUS_CANCELLED:
            today = timezone.localdate()
            cancel_days_limit = settings.BOOKING_CANCEL_DAYS_LIMIT
            limit_date = booking.check_in - timedelta(days=cancel_days_limit)
            if today > limit_date:
                raise ValueError(
                    _(
                        "You can only cancel a booking at least %(days)s days before check-in."
                    )
                    % {"days": cancel_days_limit}
                )

        booking.status = new_status
        booking.save(update_fields=["status", "updated_at"])

        if new_status == Booking.STATUS_REJECTED:
            try:
                NotificationService.send_booking_rejected_email(booking)
            except ValueError:
                pass

        return booking

    @staticmethod
    def get_client_bookings(user):
        """Obtiene el contexto con las reservas del cliente."""
        return get_client_bookings_context(user)

    @staticmethod
    def get_owner_bookings(owner):
        """Obtiene las reservas del dueño agrupadas por estado."""
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
            "rejected": bookings.filter(
                status__in=[Booking.STATUS_REJECTED, Booking.STATUS_CANCELLED]
            ),
            "past": bookings.filter(
                status=Booking.STATUS_APPROVED,
                check_out__lt=today,
            ),
        }


class PurchaseService:
    @staticmethod
    def request_purchase(property_obj, user):
        """Crea una solicitud de compra si la propiedad está disponible y el usuario puede comprarla."""
        if property_obj.listing_type != "sale":
            raise ValueError(_("This property is not for sale."))

        if property_obj.owner and property_obj.owner.user_id == user.id:
            raise ValueError(_("You cannot buy your own property."))

        if Purchase.objects.filter(
            property=property_obj,
            status=Purchase.STATUS_APPROVED,
        ).exists():
            raise ValueError(_("This property has already been sold."))

        if Purchase.objects.filter(
            property=property_obj,
            buyer=user,
        ).exists():
            raise ValueError(
                _("You already have a purchase request for this property.")
            )

        return Purchase.objects.create(
            property=property_obj,
            buyer=user,
            total_value=property_obj.price,
            status=Purchase.STATUS_PENDING,
        )

    @staticmethod
    def approve_purchase(purchase):
        """Aprueba una solicitud de compra si la propiedad no ha sido vendida."""
        if Purchase.objects.filter(
            property=purchase.property,
            status=Purchase.STATUS_APPROVED,
        ).exists():
            raise ValueError(_("This property has already been sold."))

        purchase.status = Purchase.STATUS_APPROVED
        purchase.save(update_fields=["status", "updated_at"])
        return purchase

    @staticmethod
    def reject_purchase(purchase):
        """Rechaza una solicitud de compra si está en estado pendiente."""
        if purchase.status != Purchase.STATUS_PENDING:
            raise ValueError(_("Only pending purchases can be rejected."))

        purchase.status = Purchase.STATUS_REJECTED
        purchase.save(update_fields=["status", "updated_at"])
        return purchase
