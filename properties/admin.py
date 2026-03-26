from django.contrib import admin
from django.utils.html import format_html

from .models import Property, SavedProperty


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "title",
        "city",
        "owner",
        "listing_type",
        "availability_display",
        "price",
        "rooms",
        "bathrooms",
        "image_preview",
        "created_at",
    ]
    list_filter = ["listing_type", "city"]
    search_fields = ["title", "city", "address", "owner__user__email"]
    readonly_fields = ["created_at", "image_preview", "availability_display"]
    ordering = ["-created_at"]
    fieldsets = (
        (
            "Basic information",
            {
                "fields": ("owner", "title", "description"),
            },
        ),
        (
            "Location",
            {
                "fields": ("address", "city", "latitude", "longitude"),
            },
        ),
        (
            "Details",
            {
                "fields": ("rooms", "bathrooms", "square_meters", "capacity"),
            },
        ),
        (
            "Pricing",
            {
                "fields": ("price", "listing_type", "availability_display"),
            },
        ),
        (
            "Images",
            {
                "fields": ("image", "image_url", "image_preview"),
            },
        ),
        (
            "Availability",
            {
                "fields": ("availability_dates",),
                "description": "Comma-separated blocked dates in YYYY-MM-DD format.",
            },
        ),
        (
            "Audit",
            {
                "fields": ("created_at",),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description="Availability")
    def availability_display(self, obj):
        return obj.availability_label

    @admin.display(description="Image")
    def image_preview(self, obj):
        url = obj.image.url if obj.image else obj.image_url
        if url:
            return format_html(
                '<img src="{}" style="height:60px; border-radius:4px;">',
                url,
            )
        return "-"


@admin.register(SavedProperty)
class SavedPropertyAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "property_obj", "category_display", "created_at"]
    list_filter = ["property_obj__listing_type"]
    search_fields = ["user__email", "property_obj__title"]
    readonly_fields = ["created_at", "category_display"]
    ordering = ["-created_at"]

    @admin.display(description="Category")
    def category_display(self, obj):
        return obj.category.capitalize()
