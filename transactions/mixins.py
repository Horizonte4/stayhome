from django.shortcuts import redirect
from django.http import HttpResponseForbidden


#verifica si el usuario es owner
class OwnerRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, "owner"):
            return redirect("board")
        return super().dispatch(request, *args, **kwargs)


#verifica si el owner es dueno de la propiedad
class BookingOwnerMixin:
    @staticmethod
    def is_booking_owner(request, booking):
        return (
            hasattr(request.user, "owner") and
            booking.property.owner == request.user.owner
        )