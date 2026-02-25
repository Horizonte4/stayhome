from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic.edit import UpdateView


class MessageMixin:
    """Agrega mensajes de éxito automáticos"""
    success_message = "Operación exitosa"

    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        return super().form_valid(form)


class OwnerRequiredMixin(UserPassesTestMixin):
    """Verifica que el usuario sea dueño del objeto"""
    owner_field = 'propietario'  # campo que tiene la FK al usuario

    def test_func(self):
        obj = self.get_object()
        owner = getattr(obj, self.owner_field)
        if hasattr(owner, 'usuario'):
            return owner.usuario == self.request.user
        return owner == self.request.user


class StaffRequiredMixin(UserPassesTestMixin):
    """Solo permite acceso a staff"""

    def test_func(self):
        return self.request.user.is_staff


class AjaxResponseMixin:
    """Retorna JSON si es petición AJAX"""

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(self.get_json_data(context))
        return super().render_to_response(context, **response_kwargs)

    def get_json_data(self, context):
        return {'success': True}


# Ejemplo de vista combinado (opcional):
try:
    from propiedades.models import Propiedad

    class EditarPropiedadView(LoginRequiredMixin, OwnerRequiredMixin, MessageMixin, UpdateView):
        model = Propiedad
        fields = ['titulo', 'descripcion', 'precio']
        success_message = "Propiedad actualizada correctamente"
        owner_field = 'propietario'
except Exception:
    # Si la app `propiedades` no está disponible en este momento,
    # no queremos que la importación rompa la carga del módulo core.
    EditarPropiedadView = None