from django.db import models
from django.utils import timezone
from datetime import timedelta

class PropertyManager(models.Manager):
    """
    Manager personalizado para Propiedad.
    Hereda de models.Manager para tener todos los métodos base (all, filter, get, etc.)
    """
    def available(self):
        """
        Retorna solo propiedades disponibles y con publicación activa.
        Es como hacer: Property.objects.filter(status='available', is_active=True)
        Pero encapsulado en un método reutilizable.
        """
        return self.filter(state__iexact='available', active_listing=True)

    def in_city(self, city):
        """
        Filtra propiedades disponibles por ciudad.
        Usa 'iexact' para que no importe mayúsculas/minúsculas.
        """
        return self.available().filter(city__iexact=city)

    def by_price_range(self, min_price, max_price):
        """
        Filtra propiedades disponibles por rango de precio.
        __gte = mayor o igual (>=)
        __lte = menor o igual (<=)
        """
        return self.available().filter(price__gte=min_price, price__lte=max_price)

    def recent(self, days=7):
        """
        Propiedades publicadas en los últimos X días.
        Por defecto, filtra las propiedades de los últimos 7 días.
        """
        fecha_limite = timezone.now() - timedelta(days=days)
        return self.available().filter(created_at__gte=fecha_limite)