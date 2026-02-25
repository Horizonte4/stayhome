from django.urls import path
from .views import listar_propiedades

app_name = 'propiedades'

urlpatterns = [
    path('', listar_propiedades, name='listar_propiedades'),
]
