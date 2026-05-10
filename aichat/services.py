"""Servicios de la app aichat.

Contiene dos clases con responsabilidades bien separadas:

- GeminiService: wrapper técnico sobre el SDK de Google. Solo sabe de
  formato de mensajes y de la API de Gemini.
- AssistantService: orquesta el caso de uso completo (recuperar historial,
  llamar a Gemini, persistir mensajes). No sabe NADA de cómo Gemini hace
  su trabajo — solo lo invoca.

La inyección de GeminiService dentro de AssistantService permite que en
los tests reemplacemos Gemini por un mock, sin pegar a la API real.
"""

import logging
from typing import Iterable

from django.db import transaction
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Excepciones
# ---------------------------------------------------------------------------


class GeminiServiceError(Exception):
    """Falla al comunicarse con la API de Gemini."""


class AssistantServiceError(Exception):
    """Falla en el flujo del asistente (validación, persistencia, etc.)."""


# ---------------------------------------------------------------------------
# Wrapper sobre el SDK de Gemini
# ---------------------------------------------------------------------------


class GeminiService:
    """Encapsula los detalles del SDK google-genai.

    Si Google saca un nuevo SDK mañana o decidimos cambiar a otro proveedor
    (Claude, OpenAI), solo se toca esta clase. El resto del sistema sigue
    funcionando sin cambios.
    """

    DEFAULT_MODEL = "gemini-2.5-flash"

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY no está configurada. "
                "Revisá tu archivo .env y la sección environment de docker-compose.yml."
            )
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def generate(
        self,
        history: Iterable[dict],
        user_message: str,
        system_instruction: str,
    ) -> str:
        """Genera la próxima respuesta del asistente.

        Args:
            history: lista de dicts con forma {"role": "user"|"assistant", "content": str}
                     en orden cronológico (más antiguos primero).
            user_message: el mensaje actual del usuario que aún NO está en history.
            system_instruction: instrucciones de sistema (rol, tono, reglas).

        Returns:
            Texto plano de la respuesta de Gemini.

        Raises:
            GeminiServiceError: si la API falla o devuelve respuesta vacía.
        """
        contents = self._build_contents(history, user_message)

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                ),
            )
        except Exception as exc:
            # Capturamos cualquier excepción del SDK y la envolvemos en una
            # nuestra. Así la capa de aplicación no necesita conocer las
            # excepciones internas de google-genai.
            logger.exception("Error llamando a Gemini API")
            raise GeminiServiceError(str(exc)) from exc

        text = (response.text or "").strip()
        if not text:
            raise GeminiServiceError("Gemini devolvió una respuesta vacía.")
        return text

    @staticmethod
    def _build_contents(history: Iterable[dict], user_message: str) -> list:
        """Convierte nuestro historial al formato que espera el SDK de Gemini.

        Detalle no obvio: en Gemini, el rol del asistente se llama 'model',
        no 'assistant'. Acá hacemos la traducción.
        """
        contents = []
        for msg in history:
            gemini_role = "model" if msg["role"] == "assistant" else "user"
            contents.append(
                types.Content(
                    role=gemini_role,
                    parts=[types.Part.from_text(text=msg["content"])],
                )
            )
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_message)],
            )
        )
        return contents


# ---------------------------------------------------------------------------
# Orquestador del caso de uso
# ---------------------------------------------------------------------------


# El system prompt es una plantilla con un placeholder para el idioma.
# Esto permite que la IA responda en el idioma activo del usuario sin
# duplicar prompts ni hardcodear el idioma en la lógica.
DEFAULT_SYSTEM_PROMPT_TEMPLATE = """You are the virtual assistant of StayHome, a Colombian \
platform for property rental and sale.

You help users with:
- Information about Colombian cities, areas, and neighborhoods (tourism, atmosphere, characteristics).
- General recommendations on where to stay based on their interests.
- Doubts about how to use the platform (how to book, save favorites, etc.).

Rules:
- Respond in {language_name}.
- Friendly but professional tone.
- Be concise: 4-5 sentences max unless the user asks for more detail.
- If you don't know something, say so honestly. NEVER invent specific properties, prices, \
or addresses. Property information is in the platform catalog; your role is to orient, not list inventory.
- If the user asks about topics unrelated to tourism, housing, or the platform, redirect the \
conversation kindly.
"""

# Mapeo de códigos de idioma (los que usa Django en LANGUAGES) a nombres
# legibles para el LLM. Si agregás un idioma nuevo a Django, agregalo acá.
LANGUAGE_NAMES = {
    "es": "Spanish",
    "en": "English",
}

HISTORY_LIMIT = 10  # Cuántos mensajes previos enviar como contexto a Gemini.
MAX_MESSAGE_LENGTH = 1000


class AssistantService:
    """Orquesta el procesamiento de un mensaje del chat IA.

    Recibe GeminiService por inyección, lo que permite reemplazarlo por
    un mock en tests sin tocar la red.
    """

    def __init__(
        self,
        gemini_service: GeminiService,
        system_prompt_template: str = DEFAULT_SYSTEM_PROMPT_TEMPLATE,
        history_limit: int = HISTORY_LIMIT,
    ):
        self._gemini = gemini_service
        self._system_prompt_template = system_prompt_template
        self._history_limit = history_limit

    def process_message(
        self,
        user,
        session_id,
        user_message: str,
        language: str = "es",
    ) -> dict:
        """Procesa un mensaje del usuario y devuelve la respuesta del asistente.

        Args:
            user: instancia de User autenticado (request.user).
            session_id: UUID de la sesión (string o UUID). Si es None o no
                        existe en la BD, se crea una sesión nueva.
            user_message: texto del mensaje del usuario.
            language: código del idioma activo (e.g. 'es', 'en'). La IA
                      responderá en ese idioma.

        Returns:
            dict con keys:
                - session_id (str): UUID de la sesión a devolver al cliente.
                - reply (str): respuesta generada por la IA.
                - created_at (str): timestamp ISO del mensaje del asistente.

        Raises:
            AssistantServiceError: si el mensaje es inválido o la IA falla.
            PermissionError: si el session_id pertenece a otro usuario.
        """
        from .models import AssistantMessage  # import local para evitar import circular

        clean_message = (user_message or "").strip()
        if not clean_message:
            raise AssistantServiceError("El mensaje no puede estar vacío.")
        if len(clean_message) > MAX_MESSAGE_LENGTH:
            raise AssistantServiceError(
                f"El mensaje excede el límite de {MAX_MESSAGE_LENGTH} caracteres."
            )

        session = self._get_or_create_session(user=user, session_id=session_id)
        history = self._load_history(session=session)

        # Construimos el prompt según el idioma activo. Si llega un código
        # desconocido, caemos a Spanish como default razonable.
        language_name = LANGUAGE_NAMES.get(language, "Spanish")
        system_prompt = self._system_prompt_template.format(
            language_name=language_name,
        )

        try:
            reply = self._gemini.generate(
                history=history,
                user_message=clean_message,
                system_instruction=system_prompt,
            )
        except GeminiServiceError as exc:
            raise AssistantServiceError(
                f"No se pudo generar la respuesta: {exc}"
            ) from exc

        # Guardamos los dos mensajes en una transacción: si algo falla,
        # no queda el mensaje del usuario suelto sin su respuesta asociada.
        with transaction.atomic():
            AssistantMessage.objects.create(
                session=session,
                role=AssistantMessage.ROLE_USER,
                content=clean_message,
            )
            assistant_msg = AssistantMessage.objects.create(
                session=session,
                role=AssistantMessage.ROLE_ASSISTANT,
                content=reply,
            )
            session.save(update_fields=["updated_at"])

        return {
            "session_id": str(session.session_id),
            "reply": reply,
            "created_at": assistant_msg.created_at.isoformat(),
        }

    def get_history(self, user, session_id) -> list[dict]:
        """Devuelve el historial completo de la sesión, en orden cronológico.

        Si la sesión no existe o no es del usuario, devuelve lista vacía.
        No lanza PermissionError acá: el caso "sesión ajena" es indistinguible
        del caso "sesión inexistente" desde el punto de vista del cliente.
        Esa ofuscación es una decisión de seguridad: no le decimos a un
        atacante si un session_id existe en la BD o no.
        """
        from .models import AssistantSession

        if not session_id:
            return []
        try:
            session = AssistantSession.objects.get(session_id=session_id)
        except (AssistantSession.DoesNotExist, ValueError):
            return []
        if session.user_id != user.id:
            return []
        return [
            {
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
            }
            for m in session.messages.all()
        ]

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    @staticmethod
    def _get_or_create_session(user, session_id):
        """Resuelve la sesión: la trae si existe y es del usuario, o crea una nueva."""
        from .models import AssistantSession

        if not session_id:
            return AssistantSession.objects.create(user=user)

        try:
            session = AssistantSession.objects.get(session_id=session_id)
        except (AssistantSession.DoesNotExist, ValueError):
            # ValueError = session_id mal formado. En cualquier caso, sesión nueva.
            return AssistantSession.objects.create(user=user)

        if session.user_id != user.id:
            raise PermissionError("Esta sesión pertenece a otro usuario.")
        return session

    def _load_history(self, session) -> list[dict]:
        """Devuelve los últimos N mensajes en orden cronológico."""
        recent_qs = session.messages.order_by("-created_at")[: self._history_limit]
        # reversed() para devolver de más antiguo a más reciente,
        # que es el orden que espera Gemini.
        return [
            {"role": m.role, "content": m.content} for m in reversed(list(recent_qs))
        ]
