from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Propiedad
from .forms import PropiedadForm


@login_required
def crear_propiedad(request):
    if request.method == 'POST':
        form = PropiedadForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('propiedades:listar_propiedades')
    else:
        form = PropiedadForm()

    return render(request, 'propiedades/crear.html', {'form': form})


@login_required
def eliminar_propiedad(request, pk):
    propiedad = get_object_or_404(Propiedad, pk=pk)

    if request.method == 'POST':
        propiedad.delete()
        return redirect('propiedades:listar_propiedades')

    return render(request, 'propiedades/eliminar_confirmacion.html', {'propiedad': propiedad})


@login_required
def editar_propiedad(request, pk):
    propiedad = get_object_or_404(Propiedad, pk=pk)

    if request.method == 'POST':
        form = PropiedadForm(request.POST, instance=propiedad)
        if form.is_valid():
            form.save()
            return redirect('propiedades:listar_propiedades')
    else:
        form = PropiedadForm(instance=propiedad)

    return render(request, 'propiedades/editar.html', {'form': form, 'propiedad': propiedad})


def listar_propiedades(request):
    qs = Propiedad.objects.disponibles()

    ciudad = request.GET.get('ciudad')
    min_precio = request.GET.get('min_precio')
    max_precio = request.GET.get('max_precio')

    if ciudad:
        qs = qs.en_ciudad(ciudad)

    if min_precio or max_precio:
        try:
            min_p = float(min_precio) if min_precio else 0
            max_p = float(max_precio) if max_precio else 1e12
            qs = qs.por_rango_precio(min_p, max_p)
        except (ValueError, TypeError):
            pass

    paginator = Paginator(qs, 20)
    page = request.GET.get('page')
    propiedades = paginator.get_page(page)

    return render(request, 'propiedades/lista.html', {'propiedades': propiedades})


def detalle_propiedad(request, pk):
    propiedad = get_object_or_404(Propiedad, pk=pk)
    return render(request, 'propiedades/detalle_propiedad.html', {'propiedad': propiedad})