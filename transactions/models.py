from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import TimeStampedModel, SoftDeleteModel
from properties.models import Property


class RentalApplication(TimeStampedModel, SoftDeleteModel):
    """Solicitud de arrendamiento de un cliente para una propiedad."""

    applicant = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="applications"
    )
    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.CASCADE,
        related_name="applications"
    )
    status = models.CharField(max_length=30, default="pending")
    desired_start_date = models.DateField(null=True, blank=True)
    desired_end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Application {self.id} - {self.property}"


class Contract(TimeStampedModel, SoftDeleteModel):
    """Contrato generado a partir de una solicitud o compra."""

    application = models.OneToOneField(
        RentalApplication,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="contract"
    )
    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.CASCADE,
        related_name="contracts"
    )
    tenant = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="contracts"
    )
    type = models.CharField(
        max_length=20,
        choices=(("rental", "Rental"), ("sale", "Sale"))
    )
    status = models.CharField(max_length=30, default="pending_signature")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    monthly_value = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    total_value = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    def __str__(self):
        return f"Contract {self.id} - {self.type} - {self.property}"


class PurchaseRequest(TimeStampedModel, SoftDeleteModel):
    """Solicitud de compra enviada por un cliente al propietario."""

    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_ACCEPTED, "Accepted"),
        (STATUS_REJECTED, "Rejected"),
    ]

    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.CASCADE,
        related_name="purchase_requests",
    )
    buyer = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="purchase_requests",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["property", "buyer"],
                name="unique_purchase_request_per_property_and_buyer",
            ),
        ]

    def __str__(self):
        return f"PurchaseRequest {self.id} - {self.property} - {self.status}"


class Booking(TimeStampedModel):
    """Reserva de una propiedad por un cliente."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ]

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="bookings"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings"
    )
    check_in = models.DateField()
    check_out = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    class Meta:
        ordering = ["-created_at"]

    def nights(self):
        return (self.check_out - self.check_in).days

    def __str__(self):
        return f"{self.user} - {self.property} ({self.check_in} → {self.check_out})"