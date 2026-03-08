from django.db import models
from core.models import TimeStampedModel, SoftDeleteModel
from django.conf import settings
from properties.models import Property


class RentalApplication(TimeStampedModel, SoftDeleteModel):
    applicant = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='applications')
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=30, default='pending')
    desired_start_date = models.DateField(null=True, blank=True)
    desired_end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"aplication {self.id} - {self.property}"


class Contract(TimeStampedModel, SoftDeleteModel):
    application = models.OneToOneField(RentalApplication, null=True, blank=True, on_delete=models.SET_NULL, related_name='contract')
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='contracts')
    tenant = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='contracts')
    type = models.CharField(max_length=20, choices=(('rental', 'Rental'), ('sale', 'Sale')))
    status = models.CharField(max_length=30, default='pending_signature')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    monthly_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Contract {self.id} - {self.type} - {self.property}"



class Booking(models.Model):

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

    created_at = models.DateTimeField(auto_now_add=True)

   
    def nights(self):
        return (self.check_out - self.check_in).days

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.property} ({self.check_in} → {self.check_out})"

# Para filtrar solo los activos:
# Contrato.objects.filter(is_deleted=False)