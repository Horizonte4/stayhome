from django.urls import path
from .views import (
    create_property,
    list_properties,
    edit_property,
    delete_property,
    property_detail,
)

app_name = 'properties'

urlpatterns = [
    path('create/', create_property, name='create_property'),
    path('edit/<int:pk>/', edit_property, name='edit_property'),
    path('delete/<int:pk>/', delete_property, name='delete_property'),  # Agrega esta línea
    path('<int:pk>/', property_detail, name='property_detail'),
    path('', list_properties, name='list_properties'),
]