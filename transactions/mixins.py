from django.shortcuts import redirect


class OwnerRequiredMixin:
    """Redirige al board si el usuario no es owner."""

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, "owner"):
            return redirect("board")
        return super().dispatch(request, *args, **kwargs)


class BookingOwnerMixin:
    """Verifica si el usuario es dueño de la propiedad asociada a la reserva."""

    @staticmethod
    def is_booking_owner(request, booking):
        return (
            hasattr(request.user, "owner")
            and booking.property.owner == request.user.owner
        )