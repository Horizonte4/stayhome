from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import SolicitudArriendo, Contrato


@receiver(post_save, sender=SolicitudArriendo)
def crear_contrato_al_aprobar(sender, instance, **kwargs):
    if getattr(instance, 'estado', None) == 'aprobada' and not hasattr(instance, 'contrato'):
        Contrato.objects.create(
            solicitud=instance,
            propiedad=instance.propiedad,
            inquilino=instance.solicitante,
            tipo='arriendo',
            estado='pendiente_firma'
        )