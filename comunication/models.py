from django.conf import settings
from django.db import models
from django.urls import reverse


class ConversationQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(models.Q(buyer=user) | models.Q(owner=user))

    def with_related(self):
        return self.select_related(
            "property",
            "property__owner",
            "property__owner__user",
            "buyer",
            "owner",
        )


class Conversation(models.Model):
    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.CASCADE,
        related_name="conversations",
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="buyer_conversations",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owner_conversations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ConversationQuerySet.as_manager()

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["property", "buyer"],
                name="unique_conversation_per_property_and_buyer",
            ),
        ]

    def __str__(self):
        return f"Conversation about {self.property} ({self.buyer} ↔ {self.owner})"

    def get_absolute_url(self):
        return reverse("comunication:conversation_detail", args=[self.pk])

    def is_participant(self, user):
        return user == self.buyer or user == self.owner


class MessageQuerySet(models.QuerySet):
    def with_related(self):
        return self.select_related("sender", "conversation")


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    objects = MessageQuerySet.as_manager()

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message #{self.pk} in conversation #{self.conversation_id}"