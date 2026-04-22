from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.db.models import Q

from .models import Property, SavedProperty
from .services import filter_properties_by_availability


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


def get_property_detail(pk):
    return Property.objects.with_owner().filter(pk=pk).first()


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
    return SavedProperty.objects.favorites().filter(user=user).order_by("-created_at")


def get_user_wishlist(user):
    return SavedProperty.objects.wishlist().filter(user=user).order_by("-created_at")


def list_available_properties(filters=None):
    filters = filters or {}

    queryset = Property.objects.with_owner()

    search_term = filters.get("q", "").strip()
    city = filters.get("city", "").strip()
    listing_type = filters.get("listing_type", "").strip()
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
            | Q(owner__user__first_name__icontains=search_term)
            | Q(owner__user__last_name__icontains=search_term)
        )

    if city:
        queryset = queryset.filter(Q(city__icontains=city) | Q(address__icontains=city))

    if listing_type:
        queryset = queryset.filter(listing_type=listing_type)

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

    queryset = queryset.available(check_in, check_out)
    queryset = filter_properties_by_availability(queryset, check_in, check_out)

    return queryset.order_by("-created_at")
