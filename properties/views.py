from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import date, timedelta
import calendar
from .models import Property
from .forms import PropertyForm
from transactions.models import Contract

# Crear Propiedad
@login_required
def create_property(request):
    owner = getattr(request.user, 'owner', None)
    if not owner:
        messages.error(request, 'Only property owners can create properties.')
        return redirect('home')

    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            property = form.save(commit=False)
            property.owner = owner
            property.save()
            messages.success(request, 'Property created successfully.')
            return redirect('properties:list_properties')
        else:
            messages.error(request, 'Please correct the errors below to save the property.')
    else:
        form = PropertyForm()

    return render(request, 'properties/create.html', {'form': form})

# Delete Property
@login_required
def delete_property(request, pk):
    property = get_object_or_404(Property, pk=pk)  # Retrieve the property to delete

    if request.method == 'POST':
        property.delete()  # Delete the property
        return redirect('properties:list_properties')  # Redirect to the list of properties

    return render(request, 'properties/delete_confirmation.html', {'property': property})

# Edit Property
@login_required
def edit_property(request, pk):
    property = get_object_or_404(Property, pk=pk)  # Retrieve the property to edit

    if request.method == 'POST':
        form = PropertyForm(request.POST, instance=property)  # Pass the property to the form
        if form.is_valid():
            form.save()  # Save the changes
            return redirect('properties:list_properties')  # Redirect after saving
    else:
        form = PropertyForm(instance=property)  # Pass the property to the form for editing

    return render(request, 'properties/edit.html', {'form': form, 'property': property})

# List Properties
def list_properties(request):
    qs = Property.objects.available()  # Retrieve active and available properties

    # Optional filters from query params
    city = request.GET.get('city')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    # Filtrar por ciudad, si se pasa como parámetro en la URL
    if city:
        qs = qs.en_ciudad(city)

    # Filtrar por rango de precio, si se pasa como parámetro en la URL
    if min_price or max_price:
        try:
            min_p = float(min_price) if min_price else 0
            max_p = float(max_price) if max_price else 1e12
            qs = qs.por_rango_precio(min_p, max_p)  # Aplicar el filtro por rango de precio
        except (ValueError, TypeError):
            pass  # En caso de que los valores no sean válidos, simplemente no aplicar filtro

    # Paginación
    paginator = Paginator(qs, 20)
    page = request.GET.get('page')
    properties = paginator.get_page(page)

    return render(request, 'properties/list.html', {'properties': properties})


def _month_bounds(today: date):
    first = today.replace(day=1)
    last_day = calendar.monthrange(today.year, today.month)[1]
    last = today.replace(day=last_day)
    return first, last


def _unavailable_dates(property):
    hoy = timezone.localdate()
    start_month, end_month = _month_bounds(hoy)
    contracts = property.contracts.filter(
        start_date__isnull=False,
        end_date__isnull=False,
        start_date__lte=end_month,
        end_date__gte=start_month,
    )
    blocked = set()
    for contract in contracts:
        current = max(start_month, contract.start_date)
        end = min(end_month, contract.end_date)
        while current <= end:
            blocked.add(current)
            current += timedelta(days=1)
    return blocked, start_month, end_month


def property_detail(request, pk):
    property = get_object_or_404(Property, pk=pk, active_listing=True)
    blocked, start_month, end_month = _unavailable_dates(property)

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
        'property': property,
        'days': days,
        'month_label': start_month.strftime('%B %Y'),
    }
    return render(request, 'properties/detail.html', context)
