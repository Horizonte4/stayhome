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
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'https://...'}),
    )

    def __init__(self, *args, **kwargs):
        show_active_listing = kwargs.pop('show_active_listing', True)
        super().__init__(*args, **kwargs)

        if not show_active_listing:
            self.fields.pop('active_listing', None)

        if not self.instance.pk:
            self.fields['state'].initial = 'available'
            if 'active_listing' in self.fields:
                self.fields['active_listing'].initial = True

        # Mark core fields as required on the form level
        required_fields = [
            'title', 'description', 'address', 'city', 'price', 'state', 'listing_type',
            'rooms', 'bathrooms', 'square_meters', 'capacity'
        ]
        for name in required_fields:
            if name in self.fields:
                self.fields[name].required = True

    class Meta:
        model = Property
        fields = [
            'title',
            'description',
            'address',
            'city',
            'latitude',
            'longitude',
            'price',
            'state',
            'listing_type',
            'rooms',
            'bathrooms',
            'square_meters',
            'capacity',
            'image',
            'image_url',
            'active_listing',
            'availability_dates',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Modern Downtown Apartment'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Describe highlights, amenities, nearby places...'}),
            'address': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'search location',
                'autocomplete': 'off',
                }),
            'city': forms.HiddenInput(),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),   
            'price': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'step': '0.01'}),
            'state': forms.Select(attrs={'class': 'form-input'}),
            'listing_type': forms.Select(attrs={'class': 'form-input'}),
            'rooms': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'bathrooms': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'square_meters': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'step': 1}),
            'capacity': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-input'}),
            'active_listing': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def _build_remote_image_name(self, image_url, content_type=''):
        parsed_url = urlparse(image_url)
        original_name = os.path.basename(parsed_url.path) or 'property-image'
        base_name, extension = os.path.splitext(original_name)

        if not extension:
            extension = mimetypes.guess_extension((content_type or '').split(';')[0].strip()) or '.jpg'

        safe_base_name = (base_name or 'property-image')[:60]
        return f'{safe_base_name}-{uuid.uuid4().hex[:8]}{extension}'

    def _download_image_from_url(self, image_url):
        request = Request(
            image_url,
            headers={
                'User-Agent': 'Mozilla/5.0',
                'Accept': 'image/*,*/*;q=0.8',
            },
        )

        try:
            with urlopen(request, timeout=15) as response:
                image_bytes = response.read()
                content_type = response.headers.get('Content-Type', '')
        except Exception as exc:
            raise ValidationError('Could not download the image from that URL.') from exc

        if not image_bytes:
            raise ValidationError('The image URL returned an empty file.')

        if content_type and not content_type.lower().startswith('image/'):
            raise ValidationError('The URL must point directly to an image.')

        file_name = self._build_remote_image_name(image_url, content_type)
        return ContentFile(image_bytes, name=file_name)

    def clean_image_url(self):
        image_url = (self.cleaned_data.get('image_url') or '').strip()
        if not image_url:
            return ''

        validator = URLValidator(schemes=['http', 'https'])
        try:
            validator(image_url)
        except ValidationError:
            raise forms.ValidationError('Enter a valid http or https URL.')

        return image_url

    def clean(self):
        cleaned = super().clean()

        # Numeric validations
        for field in ['price', 'rooms', 'bathrooms', 'capacity']:
            value = cleaned.get(field)
            if value is not None and value <= 0:
                self.add_error(field, 'must be greater than zero.')

        metros = cleaned.get('square_meters')
        if metros is not None and metros < 0:
            self.add_error('square_meters', 'Cannot be negative.')

        # Require at least one image source
        imagen = cleaned.get('image')
        imagen_url = cleaned.get('image_url')
        if not imagen and not imagen_url:
            self.add_error('image', 'Upload an image or provide a URL.')
            self.add_error('image_url', 'Upload an image or provide a URL.')

        if not imagen and imagen_url:
            try:
                cleaned['image'] = self._download_image_from_url(imagen_url)
                cleaned['image_url'] = ''
            except ValidationError as exc:
                self.add_error('image_url', exc)

        #  Additional validations can be added here (e.g., address format, city name, etc.)    
        lat = cleaned.get('latitude')
        lng = cleaned.get('longitude')
        address = cleaned.get('address')
        city = cleaned.get('city')

        if address and (lat is None or lng is None):
            self.add_error(
                'address',
                'Debes seleccionar una ubicación válida en el mapa.'
            )
        
        if address and not city:
            self.add_error('address', 'No se pudo detectar la ciudad. Selecciona una ubicación válida.')

        if address and not city:
            self.add_error(
                'address',
                'No se pudo detectar la ciudad. Selecciona una ubicación válida.'
            )

        return cleaned
