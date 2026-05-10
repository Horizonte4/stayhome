from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from comunication.models import Conversation, Message
from properties.models import Property
from users.models import Owner


class InboxAnonTest(TestCase):

    def test_anonimo_no_puede_ver_inbox(self):
        """Un usuario anónimo es redirigido al login al intentar ver el inbox."""
        client = Client()
        url = reverse("comunication:inbox")
        response = client.get(url)
        self.assertRedirects(response, f"/users/login/?next={url}")


class ConversationIntruderTest(TestCase):

    def setUp(self):
        user_model = get_user_model()

        self.owner_user = user_model.objects.create_user(
            email="owner@example.com",
            password="testpass123",
        )
        self.owner = Owner.objects.create(user=self.owner_user)

        self.buyer_user = user_model.objects.create_user(
            email="buyer@example.com",
            password="testpass123",
        )

        self.intruder_user = user_model.objects.create_user(
            email="intruder@example.com",
            password="testpass123",
        )

        self.property_obj = Property.objects.create(
            owner=self.owner,
            title="Casa test",
            city="Bogota",
            price=1000000,
            listing_type="sale",
        )

        self.conversation = Conversation.objects.create(
            property=self.property_obj,
            buyer=self.buyer_user,
            owner=self.owner_user,
        )

    def test_intruso_recibe_404(self):
        """Un usuario que no es parte de la conversación recibe 404."""
        client = Client()
        client.force_login(self.intruder_user)
        url = reverse(
            "comunication:conversation_detail",
            kwargs={"conversation_id": self.conversation.pk},
        )
        response = client.get(url)
        self.assertEqual(response.status_code, 404)


class SendMessageTests(TestCase):

    def setUp(self):
        user_model = get_user_model()

        self.owner_user = user_model.objects.create_user(
            email="owner2@example.com",
            password="testpass123",
        )
        self.owner = Owner.objects.create(user=self.owner_user)

        self.buyer_user = user_model.objects.create_user(
            email="buyer2@example.com",
            password="testpass123",
        )

        self.property_obj = Property.objects.create(
            owner=self.owner,
            title="Casa test",
            city="Bogota",
            price=1000000,
            listing_type="sale",
        )

        self.conversation = Conversation.objects.create(
            property=self.property_obj,
            buyer=self.buyer_user,
            owner=self.owner_user,
        )

    def test_mensaje_vacio_no_se_guarda(self):
        """Un mensaje con contenido vacío no se persiste en la base de datos."""
        client = Client()
        client.force_login(self.buyer_user)
        url = reverse(
            "comunication:send_message",
            kwargs={"conversation_id": self.conversation.pk},
        )
        client.post(url, {"content": "   "})
        self.assertEqual(
            Message.objects.filter(conversation=self.conversation).count(), 0
        )

    def test_mensajes_se_marcan_como_leidos_al_visitar(self):
        """Al visitar la conversación los mensajes no leídos del otro usuario se marcan como leídos."""
        Message.objects.create(
            conversation=self.conversation,
            sender=self.owner_user,
            content="Hola",
            is_read=False,
        )
        client = Client()
        client.force_login(self.buyer_user)
        url = reverse(
            "comunication:conversation_detail",
            kwargs={"conversation_id": self.conversation.pk},
        )
        client.get(url)
        unread = (
            Message.objects.filter(
                conversation=self.conversation,
                is_read=False,
            )
            .exclude(sender=self.buyer_user)
            .count()
        )
        self.assertEqual(unread, 0)


class StartConversationTests(TestCase):

    def setUp(self):
        user_model = get_user_model()

        self.owner_user = user_model.objects.create_user(
            email="owner3@example.com",
            password="testpass123",
        )
        self.owner = Owner.objects.create(user=self.owner_user)

        self.property_obj = Property.objects.create(
            owner=self.owner,
            title="Casa test",
            city="Bogota",
            price=1000000,
            listing_type="sale",
        )

    def test_no_se_puede_chatear_con_uno_mismo(self):
        """El propietario no puede iniciar una conversación sobre su propia propiedad."""
        client = Client()
        client.force_login(self.owner_user)
        url = reverse(
            "comunication:start_conversation",
            kwargs={"property_id": self.property_obj.pk},
        )
        response = client.post(url)
        self.assertEqual(Conversation.objects.count(), 0)
