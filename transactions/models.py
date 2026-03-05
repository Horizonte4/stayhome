from django.db import models
from core.models import TimeStampedModel, SoftDeleteModel


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


# Para filtrar solo los activos:
# Contrato.objects.filter(is_deleted=False)