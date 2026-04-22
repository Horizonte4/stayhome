from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from properties.models import Property
from transactions.models import Booking, Contract
from users.models import Owner


class PropertyAvailabilityTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner_user = user_model.objects.create_user(
            email="owner@example.com",
            password="testpass123",
            first_name="Owner",
            last_name="User",
        )
        self.owner = Owner.objects.create(user=self.owner_user)

    def test_available_manager_excludes_properties_with_sale_contract(self):
        available_property = Property.objects.create(
            owner=self.owner,
            title="Available apartment",
            city="Bogota",
            price=1000000,
            listing_type="sale",
        )
        sold_property = Property.objects.create(
            owner=self.owner,
            title="Sold apartment",
            city="Bogota",
            price=1200000,
            listing_type="sale",
        )

        Contract.objects.create(
            property=sold_property,
            tenant=self.owner_user,
            type=Contract.TYPE_SALE,
            status="completed",
            total_value=sold_property.price,
        )

        available_properties = Property.objects.available()

        self.assertIn(available_property, available_properties)
        self.assertNotIn(sold_property, available_properties)

    def test_property_is_not_available_when_blocked_dates_overlap(self):
        start_date = timezone.localdate() + timedelta(days=5)
        end_date = start_date + timedelta(days=2)

        property_obj = Property.objects.create(
            owner=self.owner,
            title="Blocked rental",
            city="Bogota",
            price=900000,
            listing_type="short_term",
            availability_dates=start_date.strftime("%Y-%m-%d"),
        )

        self.assertFalse(property_obj.is_available(start_date, end_date))

    def test_property_is_not_available_when_approved_booking_overlaps(self):
        start_date = timezone.localdate() + timedelta(days=10)
        end_date = start_date + timedelta(days=3)

        property_obj = Property.objects.create(
            owner=self.owner,
            title="Booked rental",
            city="Bogota",
            price=850000,
            listing_type="short_term",
        )

        Booking.objects.create(
            property=property_obj,
            user=self.owner_user,
            check_in=start_date,
            check_out=end_date,
            status=Booking.STATUS_APPROVED,
        )

        self.assertFalse(property_obj.is_available(start_date, end_date))
