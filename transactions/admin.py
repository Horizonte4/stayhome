from django.contrib import admin

from .models import Booking, Contract


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "property",
        "tenant",
        "type",
        "status",
        "start_date",
        "end_date",
        "created_at",
    ]
    list_filter = ["type", "status"]
    search_fields = ["tenant__email", "property__title"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
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
        return obj.nights()
