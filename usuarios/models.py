from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


# ─────────────────────────────────────────
# CUSTOM USER MANAGER
# ─────────────────────────────────────────
class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El usuario debe tener un email")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # 🔐 Encripta automáticamente
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, password, **extra_fields)


# ─────────────────────────────────────────
# USUARIO PERSONALIZADO
# ─────────────────────────────────────────
class Usuario(AbstractUser):

    username = None  # ❌ eliminamos username
    email = models.EmailField(unique=True)

    telefono = models.CharField(max_length=15, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"      # 🔥 login con email
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UsuarioManager()

    def __str__(self):
        return self.email


# ─────────────────────────────────────────
# CLIENTE
# ─────────────────────────────────────────
class Cliente(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='cliente'
    )

    def __str__(self):
        return f"Cliente: {self.usuario.email}"


# ─────────────────────────────────────────
# PROPIETARIO
# ─────────────────────────────────────────
class Propietario(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='propietario'
    )

    def __str__(self):
        return f"Propietario: {self.usuario.email}"