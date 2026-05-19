import json

from django.contrib.auth import get_user_model
from django.db.models import Count

from properties.models import Property
from transactions.models import Booking, Purchase


class ReportService:
    @staticmethod
    def generate_system_report_json(output_path="system_report.json"):
        user_model = get_user_model()

        most_booked_row = (
            Booking.objects.values("property")
            .annotate(bookings_count=Count("property"))
            .order_by("-bookings_count", "-created_at")
            .first()
        )

        most_booked_property = None
        if most_booked_row:
            property_obj = Property.objects.filter(
                pk=most_booked_row["property"]
            ).first()
            if property_obj:
                most_booked_property = {
                    "property_id": property_obj.id,
                    "title": property_obj.title,
                    "city": property_obj.city,
                    "listing_type": property_obj.listing_type,
                    "price": str(property_obj.price),
                    "bookings_count": most_booked_row["bookings_count"],
                }

        last_booking_obj = (
            Booking.objects.select_related("property", "user")
            .order_by("-created_at")
            .first()
        )
        last_booking = None
        if last_booking_obj:
            last_booking = {
                "booking_id": last_booking_obj.id,
                "property_id": last_booking_obj.property.id,
                "property_title": last_booking_obj.property.title,
                "user_id": last_booking_obj.user.id,
                "user_email": last_booking_obj.user.email,
                "check_in": last_booking_obj.check_in.isoformat(),
                "check_out": last_booking_obj.check_out.isoformat(),
                "status": last_booking_obj.status,
                "created_at": last_booking_obj.created_at.isoformat(),
            }

        last_sale_obj = (
            Purchase.objects.filter(status=Purchase.STATUS_APPROVED)
            .select_related("property", "buyer")
            .order_by("-created_at")
            .first()
        )
        last_confirmed_sale = None
        if last_sale_obj:
            last_confirmed_sale = {
                "purchase_id": last_sale_obj.id,
                "property_id": last_sale_obj.property.id,
                "property_title": last_sale_obj.property.title,
                "buyer_id": last_sale_obj.buyer.id,
                "buyer_email": last_sale_obj.buyer.email,
                "total_value": str(last_sale_obj.total_value),
                "status": last_sale_obj.status,
                "created_at": last_sale_obj.created_at.isoformat(),
            }

        payload = {
            "total_users_created": user_model.objects.count(),
            "most_booked_property": most_booked_property,
            "last_booking": last_booking,
            "last_confirmed_sale": last_confirmed_sale,
        }

        with open(output_path, "w", encoding="utf-8") as json_file:
            json.dump(payload, json_file, ensure_ascii=False, indent=2)

        return {
            "output_path": output_path,
            "report": payload,
        }
