from django.shortcuts import render
from django.core.paginator import Paginator
from .models import Propiedad


def listar_propiedades(request):
    """Vista simple para listar propiedades filtrables y paginadas."""
    qs = Propiedad.objects.disponibles()

    # Filtros opcionales desde query params
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

    # Paginación
    paginator = Paginator(qs, 20)
    page = request.GET.get('page')
    propiedades = paginator.get_page(page)

    return render(request, 'propiedades/lista.html', {'propiedades': propiedades})