# Librerías externas
from django.contrib import admin
from django.utils.timezone import now
from datetime import timedelta

# Modelos
from .models import Conversation, Message


# ── Filtro: actividad reciente de conversación ────────────────────────────────
class ConversationActivityFilter(admin.SimpleListFilter):
    title          = "actividad"
    parameter_name = "activity"

    def lookups(self, request, model_admin):
        return [
            ("today",    "Activas hoy"),
            ("week",     "Activas esta semana"),
            ("inactive", "Sin actividad hace +30 días"),
        ]

    def queryset(self, request, queryset):
        today = now()
        if self.value() == "today":
            return queryset.filter(updated_at__date=today.date())
        if self.value() == "week":
            return queryset.filter(updated_at__gte=today - timedelta(days=7))
        if self.value() == "inactive":
            return queryset.filter(updated_at__lt=today - timedelta(days=30))


# ── Filtro: mensajes no leídos ────────────────────────────────────────────────
class UnreadMessagesFilter(admin.SimpleListFilter):
    title          = "mensajes no leídos"
    parameter_name = "unread"

    def lookups(self, request, model_admin):
        return [
            ("yes", "Con mensajes no leídos"),
            ("no",  "Todos leídos"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(messages__is_read=False).distinct()
        if self.value() == "no":
            return queryset.exclude(messages__is_read=False).distinct()


# ── Filtro: fecha de mensaje ──────────────────────────────────────────────────
class MessageDateFilter(admin.SimpleListFilter):
    title          = "fecha de envío"
    parameter_name = "sent"

    def lookups(self, request, model_admin):
        return [
            ("today", "Hoy"),
            ("week",  "Últimos 7 días"),
            ("month", "Últimos 30 días"),
            ("older", "Más de 30 días"),
        ]

    def queryset(self, request, queryset):
        today = now()
        if self.value() == "today":
            return queryset.filter(created_at__date=today.date())
        if self.value() == "week":
            return queryset.filter(created_at__gte=today - timedelta(days=7))
        if self.value() == "month":
            return queryset.filter(created_at__gte=today - timedelta(days=30))
        if self.value() == "older":
            return queryset.filter(created_at__lt=today - timedelta(days=30))


# ── Inline de mensajes ────────────────────────────────────────────────────────
class MessageInline(admin.TabularInline):
    model               = Message
    extra               = 0
    readonly_fields     = ["sender", "content", "created_at", "is_read"]
    verbose_name        = "Mensaje"
    verbose_name_plural = "Mensajes"
    can_delete          = False


# ── Conversation ─────────────────────────────────────────────────────────────
@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    inlines         = [MessageInline]
    list_display    = ["id", "property", "buyer", "owner",
                       "total_messages", "unread_count", "created_at", "updated_at"]
    list_filter     = [ConversationActivityFilter, UnreadMessagesFilter]
    search_fields   = ["property__title", "buyer__email", "owner__email"]
    readonly_fields = ["created_at", "updated_at", "total_messages", "unread_count"]
    ordering        = ["-updated_at"]

    fieldsets = (
        ("Participantes", {
            "fields": ("property", "buyer", "owner")
        }),
        ("Estadísticas", {
            "fields": ("total_messages", "unread_count"),
        }),
        ("Auditoría", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    @admin.display(description="Mensajes")
    def total_messages(self, obj):
        return obj.messages.count()

    @admin.display(description="No leídos")
    def unread_count(self, obj):
        count = obj.messages.filter(is_read=False).count()
        return count if count > 0 else "—"


# ── Message ───────────────────────────────────────────────────────────────────
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display    = ["id", "sender", "conversation", "short_content",
                       "is_read", "created_at"]
    list_filter     = ["is_read", MessageDateFilter]
    list_editable   = ["is_read"]
    search_fields   = ["sender__email", "content", "conversation__property__title"]
    readonly_fields = ["created_at"]
    ordering        = ["-created_at"]

    fieldsets = (
        ("Mensaje", {
            "fields": ("conversation", "sender", "content", "is_read")
        }),
        ("Auditoría", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )

    @admin.display(description="Contenido")
    def short_content(self, obj):
        return obj.content[:60] + "..." if len(obj.content) > 60 else obj.content