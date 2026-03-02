from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Propiedad
from .forms import PropiedadForm

# Crear Propiedad
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

# Eliminar Propiedad
@login_required
def eliminar_propiedad(request, pk):
    propiedad = get_object_or_404(Propiedad, pk=pk)  # Recupera la propiedad a eliminar

    if request.method == 'POST':
        propiedad.delete()  # Elimina la propiedad
        return redirect('propiedades:listar_propiedades')  # Redirige a la lista de propiedades

    return render(request, 'propiedades/eliminar_confirmacion.html', {'propiedad': propiedad})

# Editar Propiedad
@login_required
def editar_propiedad(request, pk):
    propiedad = get_object_or_404(Propiedad, pk=pk)  # Recupera la propiedad a editar

    if request.method == 'POST':
        form = PropiedadForm(request.POST, instance=propiedad)  # Pasa la propiedad al formulario
        if form.is_valid():
            form.save()  # Guarda los cambios
            return redirect('propiedades:listar_propiedades')  # Redirige después de guardar
    else:
        form = PropiedadForm(instance=propiedad)  # Pasa la propiedad al formulario para editarla

    return render(request, 'propiedades/editar.html', {'form': form, 'propiedad': propiedad})

# Listar Propiedades
def listar_propiedades(request):
    qs = Propiedad.objects.disponibles()  # Recupera las propiedades activas y disponibles

    # Filtros opcionales desde query params
    ciudad = request.GET.get('ciudad')
    min_precio = request.GET.get('min_precio')
    max_precio = request.GET.get('max_precio')

    # Filtrar por ciudad, si se pasa como parámetro en la URL
    if ciudad:
        qs = qs.en_ciudad(ciudad)

    # Filtrar por rango de precio, si se pasa como parámetro en la URL
    if min_precio or max_precio:
        try:
            min_p = float(min_precio) if min_precio else 0
            max_p = float(max_precio) if max_precio else 1e12
            qs = qs.por_rango_precio(min_p, max_p)  # Aplicar el filtro por rango de precio
        except (ValueError, TypeError):
            pass  # En caso de que los valores no sean válidos, simplemente no aplicar filtro

    # Paginación
    paginator = Paginator(qs, 20)
    page = request.GET.get('page')
    propiedades = paginator.get_page(page)

    return render(request, 'propiedades/lista.html', {'propiedades': propiedades})
