import json
from datetime import datetime, timedelta

from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from transactions.models import Booking, Contract
from transactions.selectors import can_access_property

from .models import SavedProperty


def normalize_availability_dates(raw_dates):
    raw_dates = (raw_dates or "").strip()
    if not raw_dates:
        return "", []

    parsed_dates = []
    invalid_dates = []

    for part in raw_dates.split(","):
        value = part.strip()
        if not value:
            continue
        try:
            datetime.strptime(value, "%Y-%m-%d")
            parsed_dates.append(value)
        except ValueError:
            invalid_dates.append(value)

    if invalid_dates:
        return None, invalid_dates

    return ",".join(sorted(set(parsed_dates))), []


def get_blocked_dates(property_obj):
    return property_obj.get_blocked_dates()


def get_reserved_dates(property_obj):
    reserved_dates = set()
    approved_bookings = property_obj.bookings.filter(status=Booking.STATUS_APPROVED)

    for booking in approved_bookings:
        current_date = booking.check_in
        while current_date < booking.check_out:
            reserved_dates.add(current_date.strftime("%Y-%m-%d"))
            current_date += timedelta(days=1)

    return sorted(reserved_dates)


def filter_properties_by_availability(queryset, start_date=None, end_date=None):
    available_ids = [
        property_obj.pk
        for property_obj in queryset
        if property_obj.is_available(start_date, end_date)
    ]
    return queryset.filter(pk__in=available_ids)


def build_calendar_payload(property_obj):
    blocked_dates = [
        blocked_date.strftime("%Y-%m-%d")
        for blocked_date in get_blocked_dates(property_obj)
    ]
    reserved_dates = get_reserved_dates(property_obj)

    return {
        "blocked_dates": blocked_dates,
        "blocked_dates_json": json.dumps(blocked_dates),
        "reserved_dates": reserved_dates,
        "reserved_dates_json": json.dumps(reserved_dates),
        "all_days_available": not blocked_dates and not reserved_dates,
    }


class PropertyService:
    @staticmethod
    def validate_owner_access(user, property_obj):
        owner = getattr(user, "owner", None)

        if not owner:
            raise PermissionError(_("Only property owners can perform this action."))

        if property_obj.owner_id != owner.id:
            raise PermissionError(
                _("You cannot manage a property that is not yours.")
            )

        return True

    @staticmethod
    def create_property(form, owner, availability_dates):
        blocked_dates, invalid_dates = normalize_availability_dates(availability_dates)
        if invalid_dates:
            raise ValueError(
                _("Invalid blocked date format: ") + ", ".join(invalid_dates)
            )

        property_obj = form.save(commit=False)
        property_obj.owner = owner
        property_obj.availability_dates = blocked_dates
        property_obj.save()
        return property_obj

    @staticmethod
    def update_property(form, current_availability_dates=None):
        property_obj = form.save(commit=False)
        if current_availability_dates is not None:
            property_obj.availability_dates = current_availability_dates
        property_obj.save()
        return property_obj

    @staticmethod
    def delete_property(property_obj):
        property_obj.delete()

    @staticmethod
    def update_availability_calendar(
        property_obj,
        availability_dates,
        clear_all_dates=False,
    ):
        if clear_all_dates:
            property_obj.availability_dates = ""
            property_obj.save(update_fields=["availability_dates"])
            return property_obj

        if not (availability_dates or "").strip():
            return property_obj

        blocked_dates, invalid_dates = normalize_availability_dates(availability_dates)
        if invalid_dates:
            raise ValueError(
                _("Invalid blocked date format: ") + ", ".join(invalid_dates)
            )

        property_obj.availability_dates = blocked_dates
        property_obj.save(update_fields=["availability_dates"])
        return property_obj

    @staticmethod
    def get_blocked_dates_json(property_obj):
        blocked_dates_list = [
            blocked_date.strftime("%Y-%m-%d")
            for blocked_date in get_blocked_dates(property_obj)
        ]
        return json.dumps(sorted(blocked_dates_list))

    @staticmethod
    def toggle_saved_property(user, property_obj):
        saved_property, created = SavedProperty.objects.get_or_create(
            user=user,
            property_obj=property_obj,
        )

        if created:
            is_saved = True
            action = "added"
        else:
            saved_property.delete()
            is_saved = False
            action = "removed"

        category = "wishlist" if property_obj.listing_type == "sale" else "favorites"

        return {
            "is_saved": is_saved,
            "action": action,
            "category": category,
            "property_id": property_obj.pk,
        }

    @staticmethod
    def can_access_property(user, property_obj):
        return can_access_property(user, property_obj)

    @staticmethod
    def build_property_detail_context(user, property_obj):
        calendar_payload = build_calendar_payload(property_obj)

        is_saved = False
        has_purchased_property = False
        has_approved_booking = False
        can_contact_owner = False

        if getattr(user, "is_authenticated", False):
            is_saved = SavedProperty.objects.filter(
                user=user,
                property_obj=property_obj,
            ).exists()
            has_purchased_property = Contract.objects.filter(
                property=property_obj,
                tenant=user,
                type=Contract.TYPE_SALE,
            ).exists()
            has_approved_booking = Booking.objects.filter(
                property=property_obj,
                user=user,
                status=Booking.STATUS_APPROVED,
            ).exists()
            can_contact_owner = (
                property_obj.owner is not None
                and user != property_obj.owner.user
                and (
                    property_obj.listing_type == "sale"
                    or has_approved_booking
                    or has_purchased_property
                )
            )

        return {
            "property": property_obj,
            "is_saved": is_saved,
            "availability_label": property_obj.availability_label,
            "has_sale_contract": property_obj.has_sale_contract(),
            "has_purchased_property": has_purchased_property,
            "has_approved_booking": has_approved_booking,
            "can_contact_owner": can_contact_owner,
            "month_label": timezone.localdate().strftime("%B %Y"),
            **calendar_payload,
        }
