from django.conf import settings
from django.db import models

from core.models import SoftDeleteModel, TimeStampedModel


class Contract(TimeStampedModel, SoftDeleteModel):
    TYPE_RENTAL = "rental"
    TYPE_SALE = "sale"

    TYPE_CHOICES = (
        (TYPE_RENTAL, "Rental"),
        (TYPE_SALE, "Sale"),
    )

    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.CASCADE,
        related_name="contracts",
    )
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="contracts",
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=30, default="pending_signature")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    monthly_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    total_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"Contract {self.pk} - {self.type} - {self.property}"


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

    class Meta:
        ordering = ["-created_at"]

    def nights(self):
        return (self.check_out - self.check_in).days

    def total_price(self):
        return self.nights() * self.property.price

    def __str__(self):
        return f"{self.user} - {self.property} ({self.check_in} -> {self.check_out})"
