# Librerías externas
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UsuarioManager(BaseUserManager):
    """Manager personalizado que usa email en lugar de username."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El usuario debe tener un email")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class RoleCheckerMixin:
    """Mixin que agrega propiedades para verificar el rol del usuario."""

    @property
    def is_owner(self):
        return hasattr(self, "owner")

    @property
    def is_client(self):
        return hasattr(self, "client")

    @property
    def role(self):
        if self.is_owner:
            return "owner"
        if self.is_client:
            return "client"
        return "unknown"


class User(RoleCheckerMixin, AbstractUser):
    """Usuario personalizado que usa email como identificador único."""

    username = None
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    registration_date = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UsuarioManager()

    def __str__(self):
        return self.email


class Client(models.Model):
    """Perfil de cliente asociado a un usuario."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="client"
    )

    def __str__(self):
        return f"Client: {self.user.email}"


class Owner(models.Model):
    """Perfil de propietario asociado a un usuario."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="owner"
    )

    def __str__(self):
        return f"Owner: {self.user.email}"