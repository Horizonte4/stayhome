from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from properties.models import Property
from users.models import Owner


class StayhomeApiTests(TestCase):

    def setUp(self):
        user_model = get_user_model()
        self.owner_user = user_model.objects.create_user(
            email="owner@example.com",
            password="testpass123",
        )
        self.owner = Owner.objects.create(user=self.owner_user)

    def test_retorna_json(self):
        """El endpoint retorna una respuesta JSON válida."""
        response = Client().get(reverse("stayhome_api"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_solo_retorna_propiedades_short_y_long_term(self):
        """Solo se incluyen propiedades de arriendo, no de venta."""
        Property.objects.create(
            owner=self.owner,
            title="Arriendo corto",
            city="Bogota",
            price=500000,
            listing_type="short_term",
        )
        Property.objects.create(
            owner=self.owner,
            title="En venta",
            city="Cali",
            price=200000000,
            listing_type="sale",
        )
        response = Client().get(reverse("stayhome_api"))
        titles = [p["title"] for p in response.json()["properties"]]
        self.assertIn("Arriendo corto", titles)
        self.assertNotIn("En venta", titles)


class ProductsViewTests(TestCase):

    @patch(
        "products.views.get_products",
        return_value=[{"name": "Item 1"}, {"name": "Item 2"}],
    )
    def test_items_llegan_al_template(self, _mock):
        """Los items del servicio externo se pasan correctamente al template."""
        response = Client().get(reverse("productos_api"))
        self.assertEqual(len(response.context["items"]), 2)

    @patch("products.views.get_products", return_value=[])
    def test_post_no_permitido(self, _mock):
        """La vista solo acepta GET; un POST retorna 405."""
        response = Client().post(reverse("productos_api"))
        self.assertEqual(response.status_code, 405)
