from .models import Property, SavedProperty


def get_property_detail(pk):
    return Property.objects.detail(pk=pk)


def get_saved_property_ids(user):
    return SavedProperty.objects.ids_for_user(user)


def get_user_favorites(user):
    return SavedProperty.objects.favorites_for(user)


def get_user_wishlist(user):
    return SavedProperty.objects.wishlist_for(user)


def list_available_properties(filters=None):
    return Property.objects.search(filters)
