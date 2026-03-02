from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from propiedades.models import Propiedad
from .forms import SolicitudArriendoForm


@login_required
def request_lease(request, propiedad_id):
    propiedad = get_object_or_404(Propiedad, id=propiedad_id)

    if request.method == 'POST':
        form = SolicitudArriendoForm(request.POST)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.solicitante = request.user
            solicitud.propiedad = propiedad
            solicitud.estado = 'pendiente'
            solicitud.save()
            return redirect('propiedades:detalle_propiedad', pk=propiedad.id)
    else:
        form = SolicitudArriendoForm()

    return render(request, 'transacciones/request_lease.html', {
        'form': form,
        'propiedad': propiedad,
    })