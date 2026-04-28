import mimetypes
import os
import uuid
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.validators import URLValidator

from .models import Property


class PropertyForm(forms.ModelForm):
    image_url = forms.CharField(
        required=False,
        max_length=1000,
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "https://...",
            }
        ),
    )

    class Meta:
        model = Property
        fields = [
            "title",
            "description",
            "address",
            "city",
            "latitude",
            "longitude",
            "price",
            "listing_type",
            "rooms",
            "bathrooms",
            "square_meters",
            "capacity",
            "image",
            "image_url",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Modern Downtown Apartment",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-input",
                    "rows": 4,
                    "placeholder": "Describe highlights, amenities, nearby places...",
                }
            ),
            "address": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Search location",
                    "autocomplete": "off",
                }
            ),
            "city": forms.HiddenInput(),
            "latitude": forms.HiddenInput(),
            "longitude": forms.HiddenInput(),
            "price": forms.NumberInput(
                attrs={
                    "class": "form-input",
                    "min": 0,
                    "step": "0.01",
                }
            ),
            "listing_type": forms.Select(attrs={"class": "form-input"}),
            "rooms": forms.NumberInput(attrs={"class": "form-input", "min": 1}),
            "bathrooms": forms.NumberInput(attrs={"class": "form-input", "min": 1}),
            "square_meters": forms.NumberInput(
                attrs={
                    "class": "form-input",
                    "min": 0,
                    "step": 1,
                }
            ),
            "capacity": forms.NumberInput(attrs={"class": "form-input", "min": 1}),
            "image": forms.ClearableFileInput(attrs={"class": "form-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        required_fields = [
            "title",
            "description",
            "address",
            "city",
            "price",
            "listing_type",
            "rooms",
            "bathrooms",
            "square_meters",
            "capacity",
        ]
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True

    def _build_remote_image_name(self, image_url, content_type=""):
        parsed_url = urlparse(image_url)
        original_name = os.path.basename(parsed_url.path) or "property-image"
        base_name, extension = os.path.splitext(original_name)

        if not extension:
            extension = (
                mimetypes.guess_extension((content_type or "").split(";")[0].strip())
                or ".jpg"
            )

        safe_base_name = (base_name or "property-image")[:60]
        return f"{safe_base_name}-{uuid.uuid4().hex[:8]}{extension}"

    def _download_image_from_url(self, image_url):
        request = Request(
            image_url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "image/*,*/*;q=0.8",
            },
        )

        try:
            with urlopen(request, timeout=15) as response:  # nosec B310
                image_bytes = response.read()
                content_type = response.headers.get("Content-Type", "")
        except Exception as exc:
            raise ValidationError(
                "Could not download the image from that URL."
            ) from exc

        if not image_bytes:
            raise ValidationError("The image URL returned an empty file.")

        if content_type and not content_type.lower().startswith("image/"):
            raise ValidationError("The URL must point directly to an image.")

        file_name = self._build_remote_image_name(image_url, content_type)
        return ContentFile(image_bytes, name=file_name)

    def clean_image_url(self):
        image_url = (self.cleaned_data.get("image_url") or "").strip()
        if not image_url:
            return ""

        validator = URLValidator(schemes=["http", "https"])
        try:
            validator(image_url)
        except ValidationError as exc:
            raise forms.ValidationError("Enter a valid http or https URL.") from exc

        return image_url

    def clean(self):
        cleaned_data = super().clean()

        for field_name in ["price", "rooms", "bathrooms", "capacity"]:
            value = cleaned_data.get(field_name)
            if value is not None and value <= 0:
                self.add_error(field_name, "This value must be greater than zero.")

        square_meters = cleaned_data.get("square_meters")
        if square_meters is not None and square_meters < 0:
            self.add_error("square_meters", "This value cannot be negative.")

        image = cleaned_data.get("image")
        image_url = cleaned_data.get("image_url")
        if not image and not image_url:
            error_message = "Upload an image or provide an image URL."
            self.add_error("image", error_message)
            self.add_error("image_url", error_message)

        if not image and image_url:
            try:
                cleaned_data["image"] = self._download_image_from_url(image_url)
                cleaned_data["image_url"] = ""
            except ValidationError as exc:
                self.add_error("image_url", str(exc))

        latitude = cleaned_data.get("latitude")
        longitude = cleaned_data.get("longitude")
        address = cleaned_data.get("address")
        city = cleaned_data.get("city")

        if address and (latitude is None or longitude is None):
            self.add_error(
                "address",
                "You must select a valid location on the map.",
            )

        if address and not city:
            self.add_error(
                "address",
                "City could not be detected. Please select a valid location.",
            )

        return cleaned_data
