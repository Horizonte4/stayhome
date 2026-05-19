from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Admin para gestionar las reservas."""

    list_display = [
        "id",
        "user",
        "property",
        "check_in",
        "check_out",
        "nights_display",
        "status",
        "created_at",
    ]
    list_filter = ["status"]
    list_editable = ["status"]
    search_fields = ["user__email", "property__title"]
    readonly_fields = ["created_at", "nights_display"]
    ordering = ["-created_at"]

    @admin.display(description="Nights")
    def nights_display(self, obj):
        """Muestra el número de noches de la reserva."""
        return obj.nights()
