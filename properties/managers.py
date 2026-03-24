from datetime import timedelta

from django.db import models
from django.utils import timezone


class PropertyManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def active(self):
        return self.get_queryset().filter(active_listing=True)

    def available(self):
        return self.active().filter(state="available")

    def in_city(self, city):
        if not city:
            return self.available()
        return self.available().filter(city__iexact=city)

    def by_price_range(self, min_price=None, max_price=None):
        queryset = self.available()

        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)

        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)

        return queryset

    def recent(self, days=7):
        limit_date = timezone.now() - timedelta(days=days)
        return self.available().filter(created_at__gte=limit_date)