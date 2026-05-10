import uuid

from django.conf import settings
from django.db import models


class AssistantSession(models.Model):
    """Conversación entre un usuario y el asistente IA.

    El session_id (UUID) es lo que se expone al cliente vía localStorage.
    El user es el dueño verificado en el backend. Esta separación evita
    que un atacante adivine session_ids ajenos: aunque consiga el UUID,
    la vista valida que coincida con request.user antes de devolver datos.
    """

    session_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assistant_sessions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"AssistantSession {self.session_id} ({self.user.email})"


class AssistantMessage(models.Model):
    """Mensaje individual dentro de una sesión.

    role distingue quién habló: 'user' o 'assistant'. El orden cronológico
    se preserva con created_at para reconstruir el historial cuando se
    arma el prompt para Gemini.
    """

    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"
    ROLE_CHOICES = [
        (ROLE_USER, "User"),
        (ROLE_ASSISTANT, "Assistant"),
    ]

    session = models.ForeignKey(
        AssistantSession,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["session", "created_at"]),
        ]

    def __str__(self):
        return f"[{self.role}] {self.content[:50]}"