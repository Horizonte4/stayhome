from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import date, timedelta
import calendar
from .models import Propiedad
from .forms import PropiedadForm
from transacciones.models import Contrato

# Crear Propiedad
@login_required
def crear_propiedad(request):
    propietario = getattr(request.user, 'propietario', None)
    if not propietario:
        messages.error(request, 'Solo los propietarios pueden crear anuncios.')
        return redirect('home')

    if request.method == 'POST':
        form = PropiedadForm(request.POST, request.FILES)
        if form.is_valid():
            propiedad = form.save(commit=False)
            propiedad.propietario = propietario
            propiedad.save()
            messages.success(request, 'Propiedad creada correctamente.')
            return redirect('propiedades:listar_propiedades')
        else:
            messages.error(request, 'Corrige los errores marcados para guardar la propiedad.')
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


def _month_bounds(today: date):
    first = today.replace(day=1)
    last_day = calendar.monthrange(today.year, today.month)[1]
    last = today.replace(day=last_day)
    return first, last


def _unavailable_dates(propiedad):
    hoy = timezone.localdate()
    start_month, end_month = _month_bounds(hoy)
    contratos = propiedad.contratos.filter(
        fecha_inicio__isnull=False,
        fecha_fin__isnull=False,
        fecha_inicio__lte=end_month,
        fecha_fin__gte=start_month,
    )
    blocked = set()
    for contrato in contratos:
        current = max(start_month, contrato.fecha_inicio)
        end = min(end_month, contrato.fecha_fin)
        while current <= end:
            blocked.add(current)
            current += timedelta(days=1)
    return blocked, start_month, end_month


def detalle_propiedad(request, pk):
    propiedad = get_object_or_404(Propiedad, pk=pk, publicacion_activa=True)
    blocked, start_month, end_month = _unavailable_dates(propiedad)

    days = []
    current = start_month
    while current <= end_month:
        days.append({
            'date': current,
            'is_blocked': current in blocked,
            'is_today': current == timezone.localdate(),
        })
        current += timedelta(days=1)

    context = {
        'propiedad': propiedad,
        'days': days,
        'month_label': start_month.strftime('%B %Y'),
    }
    return render(request, 'propiedades/detalle.html', context)
