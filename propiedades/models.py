from django.db import models
from .managers import PropiedadManager


class Propiedad(models.Model):
    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('ocupado', 'Ocupado'),
        ('reservado', 'Reservado'),
    ]

    propietario = models.ForeignKey(
        'usuarios.Propietario',
        on_delete=models.CASCADE,
        related_name='propiedades',
        null=True,
        blank=True,
    )

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    ciudad = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='disponible')

    TIPO_PUBLICACION_CHOICES = [
        ('short_term', 'Short-term rental'),
        ('long_term', 'Long-term rental'),
        ('sale', 'Sale'),
    ]
    tipo_publicacion = models.CharField(max_length=20, choices=TIPO_PUBLICACION_CHOICES, default='short_term')

    habitaciones = models.PositiveSmallIntegerField(default=1)
    banos = models.PositiveSmallIntegerField(default=1)
    metros_cuadrados = models.PositiveIntegerField(null=True, blank=True)
    capacidad_personas = models.PositiveSmallIntegerField(default=1)
    imagen = models.ImageField(upload_to='propiedades/', blank=True, null=True)
    imagen_url = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    publicacion_activa = models.BooleanField(default=True)

    objects = PropiedadManager()

    def __str__(self):
        return f"{self.titulo} — {self.ciudad}"

    class Meta:
        ordering = ['-created_at']