from django.db import models
from .managers import PropiedadManager


class Propiedad(models.Model):
    titulo = models.CharField(max_length=200)
    ciudad = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    # Campo sencillo para indicar si la publicación está activa
    publicacion_activa = models.BooleanField(default=True)

    # Reemplazar el Manager por defecto
    objects = PropiedadManager()

    def __str__(self):
        return f"{self.titulo} — {self.ciudad}"

    class Meta:
        ordering = ['-created_at']