from django.urls import path

from .views import (
    create_property,
    delete_property,
    edit_calendar,
    edit_property,
    favorites_list,
    list_properties,
    property_detail,
    toggle_saved_property,
    wishlist_list,
)

app_name = "properties"

urlpatterns = [
    path("", list_properties, name="list_properties"),
    path("create/", create_property, name="create_property"),
    path("favorites/", favorites_list, name="favorites_list"),
    path("wishlist/", wishlist_list, name="wishlist_list"),
    path("<int:pk>/", property_detail, name="property_detail"),
    path("<int:pk>/edit/", edit_property, name="edit_property"),
    path("<int:pk>/calendar/", edit_calendar, name="edit_calendar"),
    path("<int:pk>/delete/", delete_property, name="delete_property"),
    path("<int:pk>/toggle-save/", toggle_saved_property, name="toggle_saved_property"),
]
