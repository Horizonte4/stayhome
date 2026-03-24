# Librerías externas
from django.contrib import admin
from django.utils.timezone import now
from datetime import timedelta, date

# Modelos
from .models import RentalApplication, PurchaseRequest, Booking


# ── Filtro: fecha de check-in de reserva ──────────────────────────────────────
class BookingCheckInFilter(admin.SimpleListFilter):
    title          = "check-in"
    parameter_name = "check_in"

    def lookups(self, request, model_admin):
        return [
            ("today",      "Hoy"),
            ("this_week",  "Esta semana"),
            ("this_month", "Este mes"),
            ("past",       "Ya realizados"),
        ]

    def queryset(self, request, queryset):
        today = date.today()
        if self.value() == "today":
            return queryset.filter(check_in=today)
        if self.value() == "this_week":
            return queryset.filter(
                check_in__gte=today,
                check_in__lte=today + timedelta(days=7)
            )
        if self.value() == "this_month":
            first = today.replace(day=1)
            last  = (first + timedelta(days=32)).replace(day=1)
            return queryset.filter(check_in__gte=first, check_in__lt=last)
        if self.value() == "past":
            return queryset.filter(check_out__lt=today)


# ── Filtro: duración de reserva en noches ────────────────────────────────────
class BookingDurationFilter(admin.SimpleListFilter):
    title          = "duración"
    parameter_name = "duration"

    def lookups(self, request, model_admin):
        return [
            ("short",  "1–3 noches"),
            ("medium", "4–7 noches"),
            ("long",   "Más de 7 noches"),
        ]

    def queryset(self, request, queryset):
        # Filtramos calculando la diferencia de fechas en Python
        ids = []
        for booking in queryset:
            nights = booking.nights()
            if self.value() == "short"  and 1 <= nights <= 3:
                ids.append(booking.pk)
            elif self.value() == "medium" and 4 <= nights <= 7:
                ids.append(booking.pk)
            elif self.value() == "long"   and nights > 7:
                ids.append(booking.pk)
        return queryset.filter(pk__in=ids) if self.value() else queryset


# ── RentalApplication ────────────────────────────────────────────────────────
@admin.register(RentalApplication)
class RentalApplicationAdmin(admin.ModelAdmin):
    list_display    = ["id", "applicant", "property", "status",
                       "desired_start_date", "desired_end_date", "created_at"]
    list_filter     = ["status"]
    search_fields   = ["applicant__email", "property__title"]
    readonly_fields = ["created_at", "updated_at"]
    ordering        = ["-created_at"]

    fieldsets = (
        ("Solicitante y propiedad", {
            "fields": ("applicant", "property")
        }),
        ("Fechas deseadas", {
            "fields": ("desired_start_date", "desired_end_date")
        }),
        ("Estado", {
            "fields": ("status",)
        }),
        ("Auditoría", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


# ── PurchaseRequest ──────────────────────────────────────────────────────────
@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display    = ["id", "buyer", "property", "status", "created_at"]
    list_filter     = ["status"]
    list_editable   = ["status"]
    search_fields   = ["buyer__email", "property__title"]
    readonly_fields = ["created_at", "updated_at"]
    ordering        = ["-created_at"]

    actions = ["aceptar_solicitudes", "rechazar_solicitudes"]

    fieldsets = (
        ("Solicitud", {
            "fields": ("property", "buyer", "status")
        }),
        ("Auditoría", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def aceptar_solicitudes(self, request, queryset):
        updated = queryset.update(status=PurchaseRequest.STATUS_ACCEPTED)
        self.message_user(request, f"{updated} solicitud(es) aceptada(s).")
    aceptar_solicitudes.short_description = "Aceptar solicitudes seleccionadas"

    def rechazar_solicitudes(self, request, queryset):
        updated = queryset.update(status=PurchaseRequest.STATUS_REJECTED)
        self.message_user(request, f"{updated} solicitud(es) rechazada(s).")
    rechazar_solicitudes.short_description = "Rechazar solicitudes seleccionadas"


# ── Booking ──────────────────────────────────────────────────────────────────
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display    = ["id", "user", "property", "check_in",
                       "check_out", "nights_display", "status", "created_at"]
    list_filter     = ["status", BookingCheckInFilter, BookingDurationFilter]
    list_editable   = ["status"]
    search_fields   = ["user__email", "property__title"]
    readonly_fields = ["created_at", "nights_display"]
    ordering        = ["-created_at"]

    actions = ["aprobar_reservas", "rechazar_reservas", "cancelar_reservas"]

    fieldsets = (
        ("Reserva", {
            "fields": ("property", "user")
        }),
        ("Fechas", {
            "fields": ("check_in", "check_out", "nights_display")
        }),
        ("Estado", {
            "fields": ("status",)
        }),
        ("Auditoría", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )

    @admin.display(description="Noches")
    def nights_display(self, obj):
        return obj.nights()

    def aprobar_reservas(self, request, queryset):
        updated = queryset.update(status="approved")
        self.message_user(request, f"{updated} reserva(s) aprobada(s).")
    aprobar_reservas.short_description = "Aprobar reservas seleccionadas"

    def rechazar_reservas(self, request, queryset):
        updated = queryset.update(status="rejected")
        self.message_user(request, f"{updated} reserva(s) rechazada(s).")
    rechazar_reservas.short_description = "Rechazar reservas seleccionadas"

    def cancelar_reservas(self, request, queryset):
        updated = queryset.update(status="cancelled")
        self.message_user(request, f"{updated} reserva(s) cancelada(s).")
    cancelar_reservas.short_description = "Cancelar reservas seleccionadas"