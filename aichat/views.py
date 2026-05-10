"""Vistas HTTP de la app aichat.

Esta capa es delgada a propósito: solo traduce HTTP <-> Python y delega
todo el trabajo a AssistantService. Así, si mañana queremos exponer el
mismo asistente como WebSocket o como un comando de management, solo
agregamos otro adaptador encima del mismo servicio.
"""

import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.translation import get_language
from django.views.decorators.http import require_GET, require_POST

from .services import (
    AssistantService,
    AssistantServiceError,
    GeminiService,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------


def _build_assistant_service() -> AssistantService:
    """Factory que construye el servicio con sus dependencias.

    Centralizar la construcción acá nos permite cambiar la implementación
    (otro modelo, otro proveedor, otra config) sin tocar la vista.
    """
    gemini = GeminiService(api_key=settings.GEMINI_API_KEY)
    return AssistantService(gemini_service=gemini)


# ---------------------------------------------------------------------------
# Vistas
# ---------------------------------------------------------------------------


@login_required
@require_POST
def send_message(request):
    """Recibe un mensaje del usuario, lo procesa con la IA y devuelve la respuesta.

    Espera body JSON: {"session_id": "<uuid o null>", "message": "<texto>"}
    Devuelve JSON: {"session_id": "<uuid>", "reply": "<texto>", "created_at": "<iso>"}
    """
    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "El cuerpo de la petición debe ser JSON válido."},
            status=400,
        )

    message = payload.get("message", "")
    session_id = payload.get("session_id") or None

    service = _build_assistant_service()

    try:
        result = service.process_message(
            user=request.user,
            session_id=session_id,
            user_message=message,
            language=get_language() or "es",
        )
    except PermissionError:
        # No queremos filtrar si la sesión existe o no: respondemos 404 genérico.
        return JsonResponse(
            {"error": "Sesión no encontrada."},
            status=404,
        )
    except AssistantServiceError as exc:
        # Errores de validación o de la IA: 400 con mensaje accionable.
        return JsonResponse({"error": str(exc)}, status=400)
    except Exception:
        # Cualquier otra cosa la registramos y devolvemos 500 sin detalles.
        # Nunca expongas el traceback al cliente: es information disclosure.
        logger.exception("Error inesperado procesando mensaje del asistente")
        return JsonResponse(
            {"error": "Error interno. Intenta más tarde."},
            status=500,
        )

    return JsonResponse(result, status=200)


@login_required
@require_GET
def history(request):
    """Devuelve los mensajes de la sesión solicitada por query param ?session_id=xxx.

    Si no hay session_id, o la sesión no existe, o pertenece a otro usuario,
    devuelve lista vacía. La ofuscación entre "no existe" y "no es tuya" es
    intencional: no queremos que un atacante pueda enumerar sesiones ajenas.
    """
    session_id = request.GET.get("session_id") or None
    service = _build_assistant_service()
    messages = service.get_history(user=request.user, session_id=session_id)
    return JsonResponse({"messages": messages})
