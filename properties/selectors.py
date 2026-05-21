from .models import Property, SavedProperty


def get_property_detail(pk):
    """Retorna el detalle de una propiedad por su ID."""
    return Property.objects.detail(pk=pk)


def get_saved_property_ids(user):
    """Retorna los IDs de las propiedades guardadas por el usuario."""
    return SavedProperty.objects.ids_for_user(user)


def get_user_favorites(user):
    """Retorna las propiedades favoritas del usuario."""
    return SavedProperty.objects.favorites_for(user)


def get_user_wishlist(user):
    """Retorna las propiedades en la lista de deseos del usuario."""
    return SavedProperty.objects.wishlist_for(user)


def list_available_properties(filters=None):
    """Retorna las propiedades disponibles según los filtros dados."""
    return Property.objects.search(filters)
