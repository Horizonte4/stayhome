from django.db import models
from .managers import PropertyManager
from django.contrib.auth import get_user_model
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


class Property(models.Model):
    STATE_CHOICES = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('reserved', 'Reserved'),
    ]

    owner = models.ForeignKey(
        'users.Owner',
        on_delete=models.CASCADE,
        related_name='properties',
        null=True,
        blank=True,
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default='available')

    listing_type = [
        ('short_term', 'Short-term rental'),
        ('long_term', 'Long-term rental'),
        ('sale', 'Sale'),
    ]
    listing_type = models.CharField(max_length=20, choices=listing_type, default='short_term')

    rooms = models.PositiveSmallIntegerField(default=1)
    bathrooms = models.PositiveSmallIntegerField(default=1)
    square_meters = models.PositiveIntegerField(null=True, blank=True)
    capacity = models.PositiveSmallIntegerField(default=1)
    image = models.ImageField(upload_to='properties/', blank=True, null=True)
    image_url = models.URLField(blank=True, max_length=1000)
    availability_dates = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    active_listing = models.BooleanField(default=True)

    objects = PropertyManager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} — {self.city}"


class Booking(models.Model):
    property = models.ForeignKey("Property", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    check_in = models.DateField()
    check_out = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.property} | {self.check_in} - {self.check_out}"


class Availability(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    availability_dates = models.DateField()

    def __str__(self):
        return f"{self.property} | {self.availability_dates}"


class SavedPropertyQuerySet(models.QuerySet):
    def with_related(self):
        return self.select_related('user', 'property_obj')

    def favorites(self):
        return self.with_related().filter(
            property_obj__listing_type__in=['short_term', 'long_term']
        )

    def wishlist(self):
        return self.with_related().filter(
            property_obj__listing_type='sale'
        )


class SavedProperty(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_properties',
    )
    property_obj = models.ForeignKey(
        'properties.Property',
        on_delete=models.CASCADE,
        related_name='saved_by_users',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = SavedPropertyQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'property_obj'],
                name='unique_saved_property_per_user',
            )
        ]

    def __str__(self):
        return f'{self.user} saved {self.property_obj}'

    @property
    def category(self):
        if self.property_obj.listing_type == 'sale':
            return 'wishlist'
        return 'favorite'

    @property
    def is_favorite(self):
        return self.property_obj.listing_type in ['short_term', 'long_term']

    @property
    def is_wishlist(self):
        return self.property_obj.listing_type == 'sale'
