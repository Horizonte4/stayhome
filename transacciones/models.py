from django.db import models
from core.models import TimeStampedModel, SoftDeleteModel


class SolicitudArriendo(TimeStampedModel, SoftDeleteModel):
    solicitante = models.ForeignKey('usuarios.Usuario', on_delete=models.CASCADE, related_name='solicitudes')
    propiedad = models.ForeignKey('propiedades.Propiedad', on_delete=models.CASCADE, related_name='solicitudes')
    estado = models.CharField(max_length=30, default='pendiente')
    fecha_inicio_deseada = models.DateField(null=True, blank=True)
    fecha_fin_deseada = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Solicitud {self.id} - {self.propiedad}"


class Contrato(TimeStampedModel, SoftDeleteModel):
    solicitud = models.OneToOneField(SolicitudArriendo, null=True, blank=True, on_delete=models.SET_NULL, related_name='contrato')
    propiedad = models.ForeignKey('propiedades.Propiedad', on_delete=models.CASCADE, related_name='contratos')
    inquilino = models.ForeignKey('usuarios.Usuario', on_delete=models.CASCADE, related_name='contratos')
    tipo = models.CharField(max_length=20, choices=(('arriendo', 'Arriendo'), ('venta', 'Venta')))
    estado = models.CharField(max_length=30, default='pendiente_firma')
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    valor_mensual = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Contrato {self.id} - {self.tipo} - {self.propiedad}"


# Para filtrar solo los activos:
# Contrato.objects.filter(is_deleted=False)