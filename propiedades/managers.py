from django.db import models
from django.utils import timezone
from datetime import timedelta

class PropiedadManager(models.Manager):
    """
    Manager personalizado para Propiedad.
    Hereda de models.Manager para tener todos los métodos base (all, filter, get, etc.)
    """
    
    def disponibles(self):
        """
        Retorna solo propiedades disponibles y con publicación activa.
        Es como hacer: Propiedad.objects.filter(estado='disponible', publicacion_activa=True)
        Pero encapsulado en un método reutilizable.
        """
        return self.filter(estado='disponible', publicacion_activa=True)
    
    def en_ciudad(self, ciudad):
        """
        Filtra propiedades disponibles por ciudad.
        Usa 'iexact' para que no importe mayúsculas/minúsculas.
        """
        return self.disponibles().filter(ciudad__iexact=ciudad)
    
    def por_rango_precio(self, min_precio, max_precio):
        """
        Filtra propiedades disponibles por rango de precio.
        __gte = mayor o igual (>=)
        __lte = menor o igual (<=)
        """
        return self.disponibles().filter(precio__gte=min_precio, precio__lte=max_precio)
    
    def recientes(self, dias=7):
        """
        Propiedades publicadas en los últimos X días.
        Por defecto, filtra las propiedades de los últimos 7 días.
        """
        fecha_limite = timezone.now() - timedelta(days=dias)
        return self.disponibles().filter(created_at__gte=fecha_limite)