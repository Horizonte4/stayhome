from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import TimeStampedModel


class BookingQuerySet(models.QuerySet):
    def with_property_details(self):
        return self.select_related(
            "property",
            "property__owner",
            "property__owner__user",
        )

    def for_user(self, user):
        return self.filter(user=user).with_property_details()

    def client_context(self, user):
        today = timezone.localdate()
        bookings = self.for_user(user)
        return {
            "pending": bookings.filter(status=Booking.STATUS_PENDING),
            "approved": bookings.filter(
                status=Booking.STATUS_APPROVED,
                check_in__gte=today,
            ),
            "rejected": bookings.filter(status=Booking.STATUS_REJECTED),
            "cancelled": bookings.filter(status=Booking.STATUS_CANCELLED),
        }


class Booking(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"

    STATUS_PENDING = Status.PENDING
    STATUS_APPROVED = Status.APPROVED
    STATUS_REJECTED = Status.REJECTED
    STATUS_CANCELLED = Status.CANCELLED

    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    check_in = models.DateField()
    check_out = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=Status,
        default=Status.PENDING,
    )

    objects = BookingQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def nights(self):
        return (self.check_out - self.check_in).days

    def total_price(self):
        return self.nights() * self.property.price

    def __str__(self):
        return f"{self.user} - {self.property} ({self.check_in} -> {self.check_out})"


class PurchaseQuerySet(models.QuerySet):
    def with_property_details(self):
        return self.select_related(
            "property",
            "property__owner",
            "property__owner__user",
        )

    def for_buyer(self, user):
        return self.filter(buyer=user).with_property_details().order_by("-created_at")

    def for_owner(self, owner):
        return (
            self.filter(property__owner=owner)
            .with_property_details()
            .order_by("-created_at")
        )


class Purchase(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    STATUS_PENDING = Status.PENDING
    STATUS_APPROVED = Status.APPROVED
    STATUS_REJECTED = Status.REJECTED

    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.CASCADE,
        related_name="purchases",
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="purchases",
    )
    total_value = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=Status,
        default=Status.PENDING,
    )

    objects = PurchaseQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.buyer} - {self.property} ({self.status})"
