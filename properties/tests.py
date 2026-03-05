from django.test import TestCase
from .models import Property

class PropertyTestCase(TestCase):
    def setUp(self):
        self.property = Property.objects.create(
            title='Apartamento Centro',
            city='Bogotá',
            price=1500000,
            estate='available'
        )

    def test_property_is_created_correctly(self):
        self.assertEqual(self.property.title, 'Apartamento Centro')
        self.assertEqual(self.property.estate, 'available')

    def test_manager_available(self):
        # Crear una propiedad no disponible
        Property.objects.create(title='Otra', city='Cali', price=1000000, estate='sold')

        available = Property.objects.available()
        self.assertEqual(available.count(), 1)
        self.assertEqual(available.first(), self.property)