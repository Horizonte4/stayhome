# Librerías externas
from django.contrib import admin
from django.utils.html import format_html

# Modelos
from .models import Property, Availability, SavedProperty


# ── Filtro: rango de precio ───────────────────────────────────────────────────
class PriceRangeFilter(admin.SimpleListFilter):
    title          = "rango de precio"
    parameter_name = "price_range"

    def lookups(self, request, model_admin):
        return [
            ("low",    "Menos de $1.000.000"),
            ("mid",    "$1.000.000 – $3.000.000"),
            ("high",   "$3.000.000 – $10.000.000"),
            ("luxury", "Más de $10.000.000"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "low":
            return queryset.filter(price__lt=1_000_000)
        if self.value() == "mid":
            return queryset.filter(price__gte=1_000_000, price__lt=3_000_000)
        if self.value() == "high":
            return queryset.filter(price__gte=3_000_000, price__lt=10_000_000)
        if self.value() == "luxury":
            return queryset.filter(price__gte=10_000_000)


# ── Filtro: tamaño por habitaciones ──────────────────────────────────────────
class RoomsFilter(admin.SimpleListFilter):
    title          = "habitaciones"
    parameter_name = "rooms"

    def lookups(self, request, model_admin):
        return [
            ("1",    "1 habitación"),
            ("2",    "2 habitaciones"),
            ("3",    "3 habitaciones"),
            ("4plus","4 o más"),
        ]

    def queryset(self, request, queryset):
        if self.value() in ("1", "2", "3"):
            return queryset.filter(rooms=int(self.value()))
        if self.value() == "4plus":
            return queryset.filter(rooms__gte=4)


# ── Filtro: tiene imagen ──────────────────────────────────────────────────────
class HasImageFilter(admin.SimpleListFilter):
    title          = "imagen"
    parameter_name = "has_image"

    def lookups(self, request, model_admin):
        return [
            ("yes", "Con imagen"),
            ("no",  "Sin imagen"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.exclude(image="", image_url="")
        if self.value() == "no":
            return queryset.filter(image="", image_url="")


# ── Inline de disponibilidad ─────────────────────────────────────────────────
class AvailabilityInline(admin.TabularInline):
    model               = Availability
    extra               = 1
    verbose_name        = "Fecha disponible"
    verbose_name_plural = "Fechas de disponibilidad"


# ── Property ─────────────────────────────────────────────────────────────────
@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    inlines         = [AvailabilityInline]
    list_display    = ["id", "title", "city", "owner", "listing_type",
                       "state", "price", "rooms", "bathrooms",
                       "active_listing", "image_preview", "created_at"]
    list_filter     = ["listing_type", "city",
                       PriceRangeFilter, RoomsFilter, HasImageFilter]
    list_editable   = ["state", "active_listing"]
    search_fields   = ["title", "city", "address", "owner__user__email"]
    readonly_fields = ["created_at", "image_preview"]
    ordering        = ["-created_at"]

    actions = ["activar_propiedades", "desactivar_propiedades"]

    fieldsets = (
        ("Información básica", {
            "fields": ("owner", "title", "description")
        }),
        ("Ubicación", {
            "fields": ("address", "city", "latitude", "longitude")
        }),
        ("Detalles", {
            "fields": ("rooms", "bathrooms", "square_meters", "capacity")
        }),
        ("Precio y tipo", {
            "fields": ("price", "listing_type", "state", "active_listing")
        }),
        ("Imágenes", {
            "fields": ("image", "image_url", "image_preview")
        }),
        ("Auditoría", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )

    @admin.display(description="Imagen")
    def image_preview(self, obj):
        url = obj.image.url if obj.image else obj.image_url
        if url:
            return format_html('<img src="{}" style="height:60px; border-radius:4px;">', url)
        return "—"

    def activar_propiedades(self, request, queryset):
        updated = queryset.update(active_listing=True)
        self.message_user(request, f"{updated} propiedad(es) activada(s).")
    activar_propiedades.short_description = "Activar propiedades seleccionadas"

    def desactivar_propiedades(self, request, queryset):
        updated = queryset.update(active_listing=False)
        self.message_user(request, f"{updated} propiedad(es) desactivada(s).")
    desactivar_propiedades.short_description = "Desactivar propiedades seleccionadas"


# ── SavedProperty ─────────────────────────────────────────────────────────────
@admin.register(SavedProperty)
class SavedPropertyAdmin(admin.ModelAdmin):
    list_display    = ["id", "user", "property_obj", "category_display", "created_at"]
    list_filter     = ["property_obj__listing_type"]
    search_fields   = ["user__email", "property_obj__title"]
    readonly_fields = ["created_at", "category_display"]
    ordering        = ["-created_at"]

    @admin.display(description="Categoría")
    def category_display(self, obj):
        return obj.category.capitalize()