# Librerías externas
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.timezone import now
from datetime import timedelta

# Modelos
from .models import User, Client, Owner

# ── Título del panel ─────────────────────────────────────────────────────────
admin.site.site_header  = "StayHome Admin"
admin.site.site_title   = "StayHome"
admin.site.index_title  = "Panel de administración"


# ── Filtro: fecha de registro ─────────────────────────────────────────────────
class RegistrationDateFilter(admin.SimpleListFilter):
    title         = "fecha de registro"
    parameter_name = "registered"

    def lookups(self, request, model_admin):
        return [
            ("today",    "Hoy"),
            ("week",     "Últimos 7 días"),
            ("month",    "Últimos 30 días"),
            ("older",    "Más de 30 días"),
        ]

    def queryset(self, request, queryset):
        today = now()
        if self.value() == "today":
            return queryset.filter(registration_date__date=today.date())
        if self.value() == "week":
            return queryset.filter(registration_date__gte=today - timedelta(days=7))
        if self.value() == "month":
            return queryset.filter(registration_date__gte=today - timedelta(days=30))
        if self.value() == "older":
            return queryset.filter(registration_date__lt=today - timedelta(days=30))


# ── Filtro: rol del usuario ───────────────────────────────────────────────────
class RoleFilter(admin.SimpleListFilter):
    title          = "rol"
    parameter_name = "role"

    def lookups(self, request, model_admin):
        return [
            ("owner",   "Propietario"),
            ("client",  "Cliente"),
            ("unknown", "Sin rol"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "owner":
            return queryset.filter(owner__isnull=False)
        if self.value() == "client":
            return queryset.filter(client__isnull=False)
        if self.value() == "unknown":
            return queryset.filter(owner__isnull=True, client__isnull=True)


# ── Inlines ──────────────────────────────────────────────────────────────────
class ClientInline(admin.StackedInline):
    model        = Client
    extra        = 0
    verbose_name = "Perfil cliente"

class OwnerInline(admin.StackedInline):
    model        = Owner
    extra        = 0
    verbose_name = "Perfil propietario"


# ── User ─────────────────────────────────────────────────────────────────────
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines         = [ClientInline, OwnerInline]
    list_display    = ["email", "first_name", "last_name", "phone",
                       "role_display", "is_staff", "is_active", "registration_date"]
    list_filter     = ["is_staff", "is_active", RoleFilter, RegistrationDateFilter]
    search_fields   = ["email", "first_name", "last_name"]
    ordering        = ["-registration_date"]
    readonly_fields = ["registration_date", "role_display"]

    fieldsets = (
        ("Credenciales", {
            "fields": ("email", "password")
        }),
        ("Información personal", {
            "fields": ("first_name", "last_name", "phone")
        }),
        ("Rol", {
            "fields": ("role_display",)
        }),
        ("Permisos", {
            "fields": ("is_active", "is_staff", "is_superuser",
                       "groups", "user_permissions"),
            "classes": ("collapse",)
        }),
        ("Auditoría", {
            "fields": ("registration_date",),
            "classes": ("collapse",)
        }),
    )

    add_fieldsets = (
        ("Nuevo usuario", {
            "fields": ("email", "first_name", "last_name",
                       "phone", "password1", "password2")
        }),
    )

    @admin.display(description="Rol")
    def role_display(self, obj):
        return obj.role.capitalize()


# ── Client ───────────────────────────────────────────────────────────────────
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display  = ["id", "get_email", "get_full_name"]
    search_fields = ["user__email", "user__first_name", "user__last_name"]

    @admin.display(description="Email")
    def get_email(self, obj):
        return obj.user.email

    @admin.display(description="Nombre")
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"


# ── Owner ─────────────────────────────────────────────────────────────────────
@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display  = ["id", "get_email", "get_full_name"]
    search_fields = ["user__email", "user__first_name", "user__last_name"]

    @admin.display(description="Email")
    def get_email(self, obj):
        return obj.user.email

    @admin.display(description="Nombre")
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"