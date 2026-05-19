from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count
from django.utils.translation import gettext as _
from django.utils import timezone
from django.conf import settings
from notifications.services import NotificationService
from properties.models import Property
from users.models import Client, Owner
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
        if purchase.status != Purchase.STATUS_PENDING:
            raise ValueError(_("Only pending purchases can be rejected."))

        purchase.status = Purchase.STATUS_REJECTED
        purchase.save(update_fields=["status", "updated_at"])
        return purchase


class ReportService:
    @staticmethod
    def get_admin_dashboard_data():
        user_model = get_user_model()

        total_users_created = user_model.objects.count()
        total_clients = Client.objects.count()
        total_owners = Owner.objects.count()
        total_properties = Property.objects.count()

        total_bookings = Booking.objects.count()
        approved_bookings = Booking.objects.filter(
            status=Booking.STATUS_APPROVED
        ).count()
        pending_bookings = Booking.objects.filter(status=Booking.STATUS_PENDING).count()
        rejected_bookings = Booking.objects.filter(
            status=Booking.STATUS_REJECTED
        ).count()
        cancelled_bookings = Booking.objects.filter(
            status=Booking.STATUS_CANCELLED
        ).count()

        total_purchases = Purchase.objects.count()
        approved_purchases = Purchase.objects.filter(
            status=Purchase.STATUS_APPROVED
        ).count()
        pending_purchases = Purchase.objects.filter(
            status=Purchase.STATUS_PENDING
        ).count()
        rejected_purchases = Purchase.objects.filter(
            status=Purchase.STATUS_REJECTED
        ).count()

        most_booked_property = (
            Booking.objects.values(
                "property",
                "property__title",
                "property__city",
                "property__listing_type",
                "property__price",
            )
            .annotate(bookings_count=Count("id"))
            .order_by("-bookings_count", "property__title")
            .first()
        )
        if most_booked_property:
            most_booked_property = {
                "property_id": most_booked_property["property"],
                "title": most_booked_property["property__title"],
                "city": most_booked_property["property__city"],
                "listing_type": most_booked_property["property__listing_type"],
                "price": most_booked_property["property__price"],
                "bookings_count": most_booked_property["bookings_count"],
            }

        top_booked_properties = list(
            Booking.objects.values("property__title")
            .annotate(bookings_count=Count("id"))
            .order_by("-bookings_count", "property__title")[:5]
        )
        max_bookings = max(
            (item["bookings_count"] for item in top_booked_properties),
            default=0,
        )
        for item in top_booked_properties:
            item["title"] = item.pop("property__title")
            item["bar_width"] = (
                (item["bookings_count"] * 100 / max_bookings) if max_bookings else 0
            )

        top_properties_by_sales = list(
            Purchase.objects.filter(status=Purchase.STATUS_APPROVED)
            .values("property__title")
            .annotate(sales_count=Count("id"))
            .order_by("-sales_count", "property__title")[:5]
        )
        max_sales = max(
            (item["sales_count"] for item in top_properties_by_sales),
            default=0,
        )
        for item in top_properties_by_sales:
            item["title"] = item.pop("property__title")
            item["bar_width"] = (
                (item["sales_count"] * 100 / max_sales) if max_sales else 0
            )

        last_booking_obj = (
            Booking.objects.select_related("property", "user")
            .order_by("-created_at")
            .first()
        )
        last_booking = None
        if last_booking_obj:
            last_booking = {
                "booking_id": last_booking_obj.id,
                "property_title": last_booking_obj.property.title,
                "user_email": last_booking_obj.user.email,
                "check_in": last_booking_obj.check_in,
                "check_out": last_booking_obj.check_out,
                "status": last_booking_obj.status,
                "created_at": last_booking_obj.created_at,
            }

        last_confirmed_sale_obj = (
            Purchase.objects.filter(status=Purchase.STATUS_APPROVED)
            .select_related("property", "buyer")
            .order_by("-created_at")
            .first()
        )
        last_confirmed_sale = None
        if last_confirmed_sale_obj:
            last_confirmed_sale = {
                "purchase_id": last_confirmed_sale_obj.id,
                "property_title": last_confirmed_sale_obj.property.title,
                "buyer_email": last_confirmed_sale_obj.buyer.email,
                "total_value": last_confirmed_sale_obj.total_value,
                "status": last_confirmed_sale_obj.status,
                "created_at": last_confirmed_sale_obj.created_at,
            }

        return {
            "summary_cards": [
                {"label": "Total users", "value": total_users_created},
                {"label": "Total clients", "value": total_clients},
                {"label": "Total owners", "value": total_owners},
                {"label": "Total properties", "value": total_properties},
                {"label": "Total bookings", "value": total_bookings},
                {"label": "Total purchases", "value": total_purchases},
            ],
            "bookings_status": {
                "approved": approved_bookings,
                "pending": pending_bookings,
                "rejected": rejected_bookings,
                "cancelled": cancelled_bookings,
            },
            "purchases_status": {
                "approved": approved_purchases,
                "pending": pending_purchases,
                "rejected": rejected_purchases,
            },
            "most_booked_property": most_booked_property,
            "top_booked_properties": top_booked_properties,
            "top_properties_by_sales": top_properties_by_sales,
            "last_booking": last_booking,
            "last_confirmed_sale": last_confirmed_sale,
        }
