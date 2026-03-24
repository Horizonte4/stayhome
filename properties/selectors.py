from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.db.models import Q

from transactions.models import Booking

from .models import Property, SavedProperty


def _parse_date(date_string):
    if not date_string:
        return None

    try:
        return datetime.strptime(date_string, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _parse_positive_int(value, minimum=1):
    if value in (None, ""):
        return None

    try:
        parsed_value = int(value)
    except (TypeError, ValueError):
        return None

    if parsed_value < minimum:
        return None

    return parsed_value


def _parse_non_negative_decimal(value):
    if value in (None, ""):
        return None

    try:
        parsed_value = Decimal(value)
    except (TypeError, InvalidOperation):
        return None

    if parsed_value < 0:
        return None

    return parsed_value


def _get_blocked_dates_set(property_obj):
    if not property_obj.availability_dates:
        return set()

    blocked_dates = set()

    for value in property_obj.availability_dates.split(","):
        value = value.strip()
        if not value:
            continue

        parsed_date = _parse_date(value)
        if parsed_date:
            blocked_dates.add(parsed_date)

    return blocked_dates


def _get_reserved_dates_set(property_obj):
    bookings = Booking.objects.filter(
        property=property_obj,
        status="approved",
    )

    reserved_dates = set()

    for booking in bookings:
        current_date = booking.check_in
        while current_date <= booking.check_out:
            reserved_dates.add(current_date)
            current_date += timedelta(days=1)

    return reserved_dates


def _is_property_available_for_range(property_obj, check_in, check_out):
    if not check_in or not check_out:
        return True

    if check_in >= check_out:
        return True

    blocked_dates = _get_blocked_dates_set(property_obj)
    reserved_dates = _get_reserved_dates_set(property_obj)

    current_date = check_in
    while current_date <= check_out:
        if current_date in blocked_dates or current_date in reserved_dates:
            return False
        current_date += timedelta(days=1)

    return True


def get_property_detail(pk):
    return (
        Property.objects.select_related("owner", "owner__user")
        .filter(pk=pk)
        .first()
    )


def get_saved_property_ids(user):
    if not getattr(user, "is_authenticated", False):
        return set()

    return set(
        SavedProperty.objects.filter(user=user).values_list(
            "property_obj_id",
            flat=True,
        )
    )


def get_user_favorites(user):
    return (
        SavedProperty.objects.favorites()
        .filter(user=user)
        .order_by("-created_at")
    )


def get_user_wishlist(user):
    return (
        SavedProperty.objects.wishlist()
        .filter(user=user)
        .order_by("-created_at")
    )


def list_available_properties(filters=None):
    filters = filters or {}

    queryset = Property.objects.available().select_related("owner", "owner__user")

    search_term = filters.get("q", "").strip()
    city = filters.get("city", "").strip()
    listing_type = filters.get("listing_type", "").strip()
    state = filters.get("state", "").strip()

    min_price = _parse_non_negative_decimal(filters.get("min_price"))
    max_price = _parse_non_negative_decimal(filters.get("max_price"))
    rooms = _parse_positive_int(filters.get("rooms"), minimum=1)
    bathrooms = _parse_positive_int(filters.get("bathrooms"), minimum=1)
    capacity = _parse_positive_int(filters.get("capacity"), minimum=1)

    check_in = _parse_date(filters.get("check_in"))
    check_out = _parse_date(filters.get("check_out"))

    if search_term:
        queryset = queryset.filter(
            Q(title__icontains=search_term)
            | Q(description__icontains=search_term)
            | Q(address__icontains=search_term)
            | Q(city__icontains=search_term)
        )

    if city:
        queryset = queryset.filter(city__icontains=city)

    if listing_type:
        queryset = queryset.filter(listing_type=listing_type)

    if state:
        queryset = queryset.filter(state=state)

    if min_price is not None:
        queryset = queryset.filter(price__gte=min_price)

    if max_price is not None:
        queryset = queryset.filter(price__lte=max_price)

    if rooms is not None:
        queryset = queryset.filter(rooms__gte=rooms)

    if bathrooms is not None:
        queryset = queryset.filter(bathrooms__gte=bathrooms)

    if capacity is not None:
        queryset = queryset.filter(capacity__gte=capacity)

    if check_in and check_out and check_in < check_out:
        available_property_ids = [
            property_obj.pk
            for property_obj in queryset
            if _is_property_available_for_range(
                property_obj=property_obj,
                check_in=check_in,
                check_out=check_out,
            )
        ]
        queryset = queryset.filter(pk__in=available_property_ids)

    return queryset.order_by("-created_at")