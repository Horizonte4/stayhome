from django.urls import path
from .views import (
    create_property,
    list_properties,
    edit_property,
    edit_calendar,
    delete_property,
    property_detail,
    toggle_saved_property,
    favorites_list,
    wishlist_list,
)

app_name = 'properties'

urlpatterns = [
    path('create/', create_property, name='create_property'),
    path('edit/<int:pk>/', edit_property, name='edit_property'),
    path('edit/<int:pk>/calendar/', edit_calendar, name='edit_calendar'),
    path('delete/<int:pk>/', delete_property, name='delete_property'),  # Agrega esta línea
    path('<int:pk>/', property_detail, name='property_detail'),
    path('', list_properties, name='list_properties'),
    path('<int:pk>/toggle-save/', toggle_saved_property, name='toggle_saved_property'),
    path('favorites/', favorites_list, name='favorites_list'),
    path('wishlist/', wishlist_list, name='wishlist_list'),
]