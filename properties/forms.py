from django import forms
from .models import Property


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = [
            'title',
            'description',
            'address',
            'city',
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
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Modern Downtown Apartment'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Describe highlights, amenities, nearby places...'}),
            'address': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '123 Main Street'}),
            'city': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Downtown'}),
            'price': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'step': '0.01'}),
            'state': forms.Select(attrs={'class': 'form-input'}),
            'listing_type': forms.Select(attrs={'class': 'form-input'}),
            'rooms': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'bathrooms': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'square_meters': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'step': 1}),
            'capacity': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-input'}),
            'image_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://...'}),
            'active_listing': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['state'].initial = 'available'
            self.fields['active_listing'].initial = True

        # Mark core fields as required on the form level
        required_fields = [
            'title', 'description', 'address', 'city', 'price', 'state', 'publication_type',
            'rooms', 'bathrooms', 'square_meters', 'capacity'
        ]
        for name in required_fields:
            if name in self.fields:
                self.fields[name].required = True

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

        return cleaned