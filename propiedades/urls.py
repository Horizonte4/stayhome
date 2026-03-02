from django.urls import path
from .views import (
    crear_propiedad,
    listar_propiedades,
    editar_propiedad,
    eliminar_propiedad,
    detalle_propiedad,
)

app_name = 'propiedades'

urlpatterns = [
    path('crear/', crear_propiedad, name='crear_propiedad'),
    path('editar/<int:pk>/', editar_propiedad, name='editar_propiedad'),
    path('eliminar/<int:pk>/', eliminar_propiedad, name='eliminar_propiedad'),
    path('<int:pk>/', detalle_propiedad, name='detalle_propiedad'),
    path('', listar_propiedades, name='listar_propiedades'),
]