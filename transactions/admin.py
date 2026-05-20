from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path

from .models import Booking
from .services import ReportService


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
    change_list_template = "admin/transactions/booking/change_list.html"
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

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "reports/",
                self.admin_site.admin_view(self.reports_dashboard_view),
                name="transactions_booking_reports",
            ),
        ]
        return custom_urls + urls

    def reports_dashboard_view(self, request):
        context = {
            **self.admin_site.each_context(request),
            "title": "Transactions reports",
            "report_data": ReportService.get_admin_dashboard_data(),
        }
        return TemplateResponse(
            request,
            "admin/transactions/reports_dashboard.html",
            context,
        )

    @admin.display(description="Nights")
    def nights_display(self, obj):
        return obj.nights()
