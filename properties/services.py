import json
from datetime import datetime, timedelta

from django.utils import timezone

from .models import SavedProperty
from transactions.models import Booking, Contract
from transactions.selectors import (
    can_access_inactive_property,
    can_contact_owner_for_property,
    get_purchase_request_for_user,
)


class PropertyService:
    @staticmethod
    def _normalize_availability_dates(raw_dates):
        raw_dates = (raw_dates or "").strip()
        if not raw_dates:
            return "", []

        parsed_dates = []
        errors = []

        for part in raw_dates.split(","):
            value = part.strip()
            if not value:
                continue

            try:
                datetime.strptime(value, "%Y-%m-%d")
                parsed_dates.append(value)
            except ValueError:
                errors.append(value)

        if errors:
            return None, errors

        normalized_dates = ",".join(sorted(set(parsed_dates)))
        return normalized_dates, []

    @staticmethod
    def _get_blocked_dates(property_obj):
        if not property_obj.availability_dates:
            return set()

        blocked_dates = set()
        dates = property_obj.availability_dates.split(",")

        for value in dates:
            value = value.strip()
            if not value:
                continue

            blocked_dates.add(
                datetime.strptime(value, "%Y-%m-%d").date()
            )

        return blocked_dates

    @staticmethod
    def _get_reserved_dates(property_obj):
        bookings = Booking.objects.filter(
            property=property_obj,
            status="approved",
        )

        reserved_dates = set()

        for booking in bookings:
            current = booking.check_in
            while current <= booking.check_out:
                reserved_dates.add(current.strftime("%Y-%m-%d"))
                current += timedelta(days=1)

        return sorted(reserved_dates)

    @staticmethod
    def validate_owner_access(user, property_obj):
        owner = getattr(user, "owner", None)

        if not owner:
            raise PermissionError(
                "Only property owners can perform this action."
            )

        if property_obj.owner_id != owner.id:
            raise PermissionError(
                "You cannot manage a property that is not yours."
            )

        return True

    @staticmethod
    def create_property(form, owner, availability_dates):
        blocked_dates, invalid_dates = PropertyService._normalize_availability_dates(
            availability_dates
        )

        if invalid_dates:
            raise ValueError(
                "Invalid blocked date format: " + ", ".join(invalid_dates)
            )

        property_obj = form.save(commit=False)
        property_obj.owner = owner
        property_obj.active_listing = True
        property_obj.availability_dates = blocked_dates
        property_obj.save()

        return property_obj

    @staticmethod
    def update_property(form):
        return form.save()

    @staticmethod
    def delete_property(property_obj):
        property_obj.delete()

    @staticmethod
    def update_availability_calendar(property_obj, availability_dates):
        blocked_dates, invalid_dates = PropertyService._normalize_availability_dates(
            availability_dates
        )

        if invalid_dates:
            raise ValueError(
                "Invalid blocked date format: " + ", ".join(invalid_dates)
            )

        property_obj.availability_dates = blocked_dates
        property_obj.save(update_fields=["availability_dates"])

        return property_obj

    @staticmethod
    def get_blocked_dates_json(property_obj):
        blocked_dates = PropertyService._get_blocked_dates(property_obj)
        blocked_dates_list = sorted(
            [blocked_date.strftime("%Y-%m-%d") for blocked_date in blocked_dates]
        )
        return json.dumps(blocked_dates_list)

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

        category = (
            "wishlist"
            if property_obj.listing_type == "sale"
            else "favorites"
        )

        return {
            "is_saved": is_saved,
            "action": action,
            "category": category,
            "property_id": property_obj.pk,
        }

    @staticmethod
    def can_access_property(user, property_obj):
        return can_access_inactive_property(user, property_obj)

    @staticmethod
    def build_property_detail_context(user, property_obj):
        today = timezone.localdate()

        start_month = today.replace(day=1)
        end_month = (
            (start_month + timedelta(days=32)).replace(day=1)
            - timedelta(days=1)
        )

        blocked_dates = PropertyService._get_blocked_dates(property_obj)
        reserved_dates = PropertyService._get_reserved_dates(property_obj)

        is_saved = False
        has_purchased_property = False
        has_approved_booking = False
        purchase_request = None
        can_contact_owner = False

        if getattr(user, "is_authenticated", False):
            is_saved = SavedProperty.objects.filter(
                user=user,
                property_obj=property_obj,
            ).exists()

            has_purchased_property = Contract.objects.filter(
                property=property_obj,
                tenant=user,
                type="sale",
            ).exists()

            has_approved_booking = Booking.objects.filter(
                property=property_obj,
                user=user,
                status="approved",
            ).exists()

            purchase_request = get_purchase_request_for_user(property_obj, user)

            can_contact_owner = (
                has_approved_booking
                or can_contact_owner_for_property(user, property_obj)
            )

        can_request_purchase = (
            property_obj.listing_type == "sale"
            and property_obj.active_listing
            and property_obj.state == "available"
            and getattr(user, "is_authenticated", False)
            and property_obj.owner
            and user != property_obj.owner.user
            and not has_purchased_property
            and (
                purchase_request is None
                or purchase_request.status == "rejected"
            )
        )

        blocked_dates_json = json.dumps(
            [blocked_date.strftime("%Y-%m-%d") for blocked_date in blocked_dates]
        )
        reserved_dates_json = json.dumps(reserved_dates)

        all_days_available = not blocked_dates and not reserved_dates

        days = []
        current = start_month

        while current <= end_month:
            is_available = (
                all_days_available
                or (
                    current not in blocked_dates
                    and current.strftime("%Y-%m-%d") not in reserved_dates
                )
            )

            days.append(
                {
                    "date": current,
                    "is_available": is_available,
                    "is_today": current == today,
                }
            )
            current += timedelta(days=1)

        return {
            "property": property_obj,
            "is_saved": is_saved,
            "days": days,
            "month_label": today.strftime("%B %Y"),
            "blocked_dates_json": blocked_dates_json,
            "reserved_dates_json": reserved_dates_json,
            "all_days_available": all_days_available,
            "can_contact_owner": can_contact_owner,
            "has_purchased_property": has_purchased_property,
            "purchase_request": purchase_request,
            "can_request_purchase": can_request_purchase,
        }