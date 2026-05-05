from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.db import models
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone


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


class PropertyQuerySet(models.QuerySet):
    def with_owner(self):
        return self.select_related("owner", "owner__user")

    def available(self, start_date=None, end_date=None):
        from transactions.models import Booking, Contract

        if start_date is None or end_date is None:
            start_date = timezone.localdate()
            end_date = start_date + timedelta(days=1)

        sold_contracts = Contract.objects.filter(
            property_id=OuterRef("pk"),
            type=Contract.TYPE_SALE,
        )
        approved_booking_conflicts = Booking.objects.filter(
            property_id=OuterRef("pk"),
            status=Booking.STATUS_APPROVED,
            check_in__lt=end_date,
            check_out__gt=start_date,
        )

        return (
            self.annotate(
                has_sale_contract_flag=Exists(sold_contracts),
                has_booking_conflict_flag=Exists(approved_booking_conflicts),
            )
            .filter(has_sale_contract_flag=False)
            .exclude(
                listing_type__in=["short_term", "long_term"],
                has_booking_conflict_flag=True,
            )
        )

    def in_city(self, city, start_date=None, end_date=None):
        return self.available(start_date, end_date).filter(city__iexact=city)

    def by_price_range(self, min_price, max_price, start_date=None, end_date=None):
        return self.available(start_date, end_date).filter(
            price__gte=min_price,
            price__lte=max_price,
        )

    def recent(self, days=7, start_date=None, end_date=None):
        limit_date = timezone.now() - timedelta(days=days)
        return self.available(start_date, end_date).filter(created_at__gte=limit_date)

    def detail(self, pk):
        return self.with_owner().filter(pk=pk).first()

    def search(self, filters=None):
        from .services import filter_properties_by_availability

        filters = filters or {}
        queryset = self.with_owner()

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
            queryset = queryset.filter(
                Q(city__icontains=city) | Q(address__icontains=city)
            )

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


class PropertyManager(models.Manager.from_queryset(PropertyQuerySet)):
    pass