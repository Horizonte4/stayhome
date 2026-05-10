from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from users.models import Client as ClientProfile, Owner


class RegisterViewTests(TestCase):
    def test_registro_crea_usuario_con_rol_client(self):
        """Al registrarse como cliente se crea el usuario y su perfil Client."""
        client = Client()
        response = client.post(
            reverse("registration"),
            {
                "email": "cliente@example.com",
                "password1": "testpass123!",
                "password2": "testpass123!",
                "user_type": "client",
            },
        )
        user = get_user_model().objects.get(email="cliente@example.com")
        self.assertTrue(ClientProfile.objects.filter(user=user).exists())

    def test_registro_crea_usuario_con_rol_owner(self):
        """Al registrarse como owner se crea el usuario y su perfil Owner."""
        client = Client()
        client.post(
            reverse("registration"),
            {
                "email": "owner@example.com",
                "password1": "testpass123!",
                "password2": "testpass123!",
                "user_type": "owner",
            },
        )
        user = get_user_model().objects.get(email="owner@example.com")
        self.assertTrue(Owner.objects.filter(user=user).exists())


class LoginViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="testpass123",
        )

    def test_login_correcto_redirige_al_home(self):
        """Con credenciales válidas el usuario es redirigido al home."""
        client = Client()
        response = client.post(
            reverse("login"),
            {
                "username": "user@example.com",
                "password": "testpass123",
            },
        )
        self.assertRedirects(response, reverse("home"))

    def test_login_incorrecto_no_autentica(self):
        """Con contraseña incorrecta el usuario no queda autenticado."""
        client = Client()
        client.post(
            reverse("login"),
            {
                "username": "user@example.com",
                "password": "wrongpassword",
            },
        )
        self.assertFalse(client.session.get("_auth_user_id"))
