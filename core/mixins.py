from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic.edit import UpdateView


class MessageMixin:
    """adds automatic success message on form_valid"""

    success_message = "Operation successful"

    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        return super().form_valid(form)


class OwnerRequiredMixin(UserPassesTestMixin):
    """checks if the logged in user is the owner of the object"""

    owner_field = "owner"  # campo que tiene la FK al usuario

    def test_func(self):
        obj = self.get_object()
        owner = getattr(obj, self.owner_field)
        if hasattr(owner, "user"):
            return owner.user == self.request.user
        return owner == self.request.user


class StaffRequiredMixin(UserPassesTestMixin):
    """only allows access to staff users"""

    def test_func(self):
        return self.request.user.is_staff


class AjaxResponseMixin:
    """Returns JSON if the request is AJAX"""

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(self.get_json_data(context))
        return super().render_to_response(context, **response_kwargs)

    def get_json_data(self, context):
        return {"success": True}


# Ejemplo de vista combinado (opcional):
try:
    from properties.models import Property

    class EditPropertyView(
        LoginRequiredMixin, OwnerRequiredMixin, MessageMixin, UpdateView
    ):
        model = Property
        fields = ["title", "description", "price"]
        success_message = "Property updated successfully"
        owner_field = "owner"
except Exception:
    # Si la app `propierties` no está disponible en este momento,
    # no queremos que la importación rompa la carga del módulo core.
    EditPropertyView = None
