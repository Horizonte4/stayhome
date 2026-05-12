from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase, Client
from django.urls import reverse

from properties.models import Property
from transactions.models import Booking
from users.models import Owner


def make_user(email):
    return get_user_model().objects.create_user(
        email=email,
        password="testpass123",
    )


class CreateBookingTests(TestCase):
    def setUp(self):
        self.owner_user = make_user("owner@example.com")
        self.owner = Owner.objects.create(user=self.owner_user)
        self.buyer_user = make_user("buyer@example.com")
        self.property_obj = Property.objects.create(
            owner=self.owner,
            title="Casa test",
            city="Bogota",
            price=500000,
            listing_type="short_term",
        )
        self.url = reverse(
            "transactions:create_booking", kwargs={"property_id": self.property_obj.pk}
        )

    def test_fechas_vacias_muestran_error(self):
        """Sin fechas se muestra un mensaje de error."""
        client = Client()
        client.force_login(self.buyer_user)
        response = client.post(self.url, {"check_in": "", "check_out": ""})
        msgs = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("Must select check in and check out.", msgs)

    def test_checkout_antes_de_checkin_muestra_error(self):
        """Si check-out es anterior a check-in se muestra un error."""
        client = Client()
        client.force_login(self.buyer_user)
        response = client.post(
            self.url, {"check_in": "2026-06-10", "check_out": "2026-06-05"}
        )
        msgs = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("Check-out must be later than check-in.", msgs)

    def test_anonimo_es_redirigido_al_login(self):
        """Un usuario anónimo es redirigido al login."""
        response = Client().post(
            self.url, {"check_in": "2026-06-01", "check_out": "2026-06-05"}
        )
        self.assertRedirects(response, f"/users/login/?next={self.url}")


class ChangeBookingStatusTests(TestCase):
    def setUp(self):
        self.owner_user = make_user("owner@example.com")
        self.owner = Owner.objects.create(user=self.owner_user)
        self.buyer_user = make_user("buyer@example.com")
        self.intruder = make_user("intruder@example.com")

        property_obj = Property.objects.create(
            owner=self.owner,
            title="Casa test",
            city="Bogota",
            price=500000,
            listing_type="short_term",
        )
        self.booking = Booking.objects.create(
            property=property_obj,
            user=self.buyer_user,
            check_in="2026-07-01",
            check_out="2026-07-05",
            status=Booking.STATUS_PENDING,
        )

    def test_intruso_no_puede_cambiar_estado(self):
        """Un usuario ajeno a la reserva recibe un mensaje de error."""
        client = Client()
        client.force_login(self.intruder)
        url = reverse(
            "transactions:change_booking_status",
            kwargs={
                "booking_id": self.booking.pk,
                "new_status": Booking.STATUS_APPROVED,
            },
        )
        response = client.get(url)
        msgs = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("You are not allowed to change this booking.", msgs)

    def test_comprador_puede_cancelar_su_reserva(self):
        """El comprador puede cancelar su propia reserva."""
        client = Client()
        client.force_login(self.buyer_user)
        url = reverse(
            "transactions:change_booking_status",
            kwargs={
                "booking_id": self.booking.pk,
                "new_status": Booking.STATUS_CANCELLED,
            },
        )
        client.get(url)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.STATUS_CANCELLED)
