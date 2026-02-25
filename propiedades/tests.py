from django.test import TestCase
from .models import Propiedad

class PropiedadTestCase(TestCase):
    def setUp(self):
        self.propiedad = Propiedad.objects.create(
            titulo='Apartamento Centro',
            ciudad='Bogotá',
            precio=1500000,
            estado='disponible'
        )
    
    def test_propiedad_se_crea_correctamente(self):
        self.assertEqual(self.propiedad.titulo, 'Apartamento Centro')
        self.assertEqual(self.propiedad.estado, 'disponible')
    
    def test_manager_disponibles(self):
        # Crear una propiedad no disponible
        Propiedad.objects.create(titulo='Otra', ciudad='Cali', precio=1000000, estado='vendida')
        
        disponibles = Propiedad.objects.disponibles()
        self.assertEqual(disponibles.count(), 1)
        self.assertEqual(disponibles.first(), self.propiedad)