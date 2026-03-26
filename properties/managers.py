from datetime import timedelta

from django.db import models
from django.db.models import Exists, OuterRef
from django.utils import timezone


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


class PropertyManager(models.Manager.from_queryset(PropertyQuerySet)):
    pass
