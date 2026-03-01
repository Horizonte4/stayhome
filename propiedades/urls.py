from django.urls import path
from .views import listar_propiedades, detalle_propiedad

app_name = 'propiedades'

urlpatterns = [
    path('', listar_propiedades, name='listar_propiedades'),
    path('<int:pk>/', detalle_propiedad, name='detalle_propiedad'),
]