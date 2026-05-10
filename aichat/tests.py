"""Tests unitarios de los servicios del asistente.

GeminiService está mockeado en todos los tests. NUNCA pegamos a la API
real desde tests: es lento, cuesta cuota, y los tests deben ser
determinísticos.
"""

from unittest.mock import MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import AssistantMessage, AssistantSession
from .services import (
    AssistantService,
    AssistantServiceError,
    GeminiService,
    GeminiServiceError,
)

User = get_user_model()


class AssistantServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        self.gemini_mock = MagicMock(spec=GeminiService)
        self.gemini_mock.generate.return_value = "Respuesta mock del asistente."
        self.service = AssistantService(gemini_service=self.gemini_mock)

    def test_creates_new_session_when_no_session_id_provided(self):
        result = self.service.process_message(
            user=self.user,
            session_id=None,
            user_message="Hola",
        )

        self.assertIn("session_id", result)
        self.assertEqual(result["reply"], "Respuesta mock del asistente.")
        self.assertEqual(AssistantSession.objects.count(), 1)
        self.assertEqual(AssistantMessage.objects.count(), 2)  # user + assistant

    def test_reuses_existing_session(self):
        session = AssistantSession.objects.create(user=self.user)

        self.service.process_message(
            user=self.user,
            session_id=str(session.session_id),
            user_message="primer mensaje",
        )
        self.service.process_message(
            user=self.user,
            session_id=str(session.session_id),
            user_message="segundo mensaje",
        )

        self.assertEqual(AssistantSession.objects.count(), 1)
        self.assertEqual(session.messages.count(), 4)

    def test_rejects_session_belonging_to_another_user(self):
        other_user = User.objects.create_user(
            email="other@example.com",
            password="x",
            first_name="A",
            last_name="B",
        )
        other_session = AssistantSession.objects.create(user=other_user)

        with self.assertRaises(PermissionError):
            self.service.process_message(
                user=self.user,
                session_id=str(other_session.session_id),
                user_message="Hola",
            )

    def test_rejects_empty_message(self):
        with self.assertRaises(AssistantServiceError):
            self.service.process_message(
                user=self.user,
                session_id=None,
                user_message="   ",
            )

    def test_rejects_message_over_limit(self):
        with self.assertRaises(AssistantServiceError):
            self.service.process_message(
                user=self.user,
                session_id=None,
                user_message="x" * 1001,
            )

    def test_passes_history_to_gemini_in_chronological_order(self):
        session = AssistantSession.objects.create(user=self.user)
        AssistantMessage.objects.create(session=session, role="user", content="primero")
        AssistantMessage.objects.create(
            session=session, role="assistant", content="respuesta1"
        )

        self.service.process_message(
            user=self.user,
            session_id=str(session.session_id),
            user_message="tercero",
        )

        history = self.gemini_mock.generate.call_args.kwargs["history"]
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["content"], "primero")
        self.assertEqual(history[1]["content"], "respuesta1")

    def test_wraps_gemini_error_in_assistant_service_error(self):
        self.gemini_mock.generate.side_effect = GeminiServiceError("API down")

        with self.assertRaises(AssistantServiceError):
            self.service.process_message(
                user=self.user,
                session_id=None,
                user_message="Hola",
            )

    def test_unknown_session_id_creates_new_session(self):
        import uuid

        result = self.service.process_message(
            user=self.user,
            session_id=str(uuid.uuid4()),  # UUID válido pero no existe en BD
            user_message="Hola",
        )

        self.assertEqual(AssistantSession.objects.count(), 1)
        self.assertIsNotNone(result["session_id"])
