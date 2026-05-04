from datetime import datetime, timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .managers import PropertyManager


class Property(models.Model):
    LISTING_TYPE_CHOICES = [
        ("short_term", _("Short-term rental")),
        ("long_term", _("Long-term rental")),
        ("sale", _("Sale")),
    ]

    owner = models.ForeignKey(
        "users.Owner",
        on_delete=models.CASCADE,
        related_name="properties",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    price = models.DecimalField(max_digits=12, decimal_places=2)
    listing_type = models.CharField(
        max_length=20,
        choices=LISTING_TYPE_CHOICES,
        default="short_term",
    )
    rooms = models.PositiveSmallIntegerField(default=1)
    bathrooms = models.PositiveSmallIntegerField(default=1)
    square_meters = models.PositiveIntegerField(null=True, blank=True)
    capacity = models.PositiveSmallIntegerField(default=1)
    image = models.ImageField(upload_to="properties/", blank=True, null=True)
    image_url = models.URLField(blank=True, max_length=1000)
    availability_dates = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = PropertyManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.city}"

    def get_blocked_dates(self):
        if not self.availability_dates:
            return set()

        blocked_dates = set()
        for raw_date in self.availability_dates.split(","):
            value = raw_date.strip()
            if not value:
                continue
            blocked_dates.add(datetime.strptime(value, "%Y-%m-%d").date())

        return blocked_dates

    def has_sale_contract(self):
        from transactions.models import Contract

        return Contract.objects.filter(
            property=self,
            type=Contract.TYPE_SALE,
        ).exists()

    def has_approved_booking_overlap(self, start_date, end_date):
        if self.listing_type == "sale":
            return False

        from transactions.models import Booking

        return self.bookings.filter(
            status=Booking.STATUS_APPROVED,
            check_in__lt=end_date,
            check_out__gt=start_date,
        ).exists()

    def has_blocked_dates_overlap(self, start_date, end_date):
        if self.listing_type == "sale":
            return False

        current_date = start_date
        blocked_dates = self.get_blocked_dates()

        while current_date < end_date:
            if current_date in blocked_dates:
                return True
            current_date += timedelta(days=1)

        return False

    def is_available(self, start_date=None, end_date=None):
        if self.has_sale_contract():
            return False

        if self.listing_type == "sale":
            return True

        if start_date is None or end_date is None:
            start_date = timezone.localdate()
            end_date = start_date + timedelta(days=1)

        return not (
            self.has_blocked_dates_overlap(start_date, end_date)
            or self.has_approved_booking_overlap(start_date, end_date)
        )

    @property
    def availability_label(self):
        if self.has_sale_contract():
            return _("Sold")

        if self.listing_type == "sale":
            return _("Available")

        return _("Available") if self.is_available() else _("Unavailable")


class SavedPropertyQuerySet(models.QuerySet):
    def with_related(self):
        return self.select_related("user", "property_obj")

    def favorites(self):
        return self.with_related().filter(
            property_obj__listing_type__in=["short_term", "long_term"]
        )

    def wishlist(self):
        return self.with_related().filter(property_obj__listing_type="sale")


class SavedProperty(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_properties",
    )
    property_obj = models.ForeignKey(
        "properties.Property",
        on_delete=models.CASCADE,
        related_name="saved_by_users",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = SavedPropertyQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "property_obj"],
                name="unique_saved_property_per_user",
            )
        ]

    def __str__(self):
        return f"{self.user} saved {self.property_obj}"

    @property
    def category(self):
        if self.property_obj.listing_type == "sale":
            return "wishlist"
        return "favorite"

    @property
    def is_favorite(self):
        return self.property_obj.listing_type in ["short_term", "long_term"]

    @property
    def is_wishlist(self):
        return self.property_obj.listing_type == "sale"
