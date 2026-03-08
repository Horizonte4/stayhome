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
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.db.models import Q

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
@require_http_methods(["GET", "POST"])
def delete_property(request, pk):
    prop = get_object_or_404(Property, pk=pk)

    # Solo owners pueden borrar
    owner = getattr(request.user, "owner", None)
    if not owner:
        messages.error(request, "You do not have permission to delete properties.")
        return HttpResponseForbidden("Forbidden")

    # Solo puede borrar sus propiedades
    if prop.owner_id != owner.id:
        return HttpResponseForbidden("You cannot delete a property that is not yours.")

    if request.method == "POST":
        prop.delete()
        messages.success(request, "Property deleted successfully.")
        return redirect("properties:list_properties")

    # GET -> confirmación
    return render(request, "properties/delete_confirmation.html", {"property": prop})

# Edit Property
@login_required
def edit_property(request, pk):
    prop = get_object_or_404(Property, pk=pk)

    # Solo owners pueden editar
    owner = getattr(request.user, "owner", None)
    if not owner:
        messages.error(request, "You do not have permission to edit properties.")
        return HttpResponseForbidden("Forbidden")

    # Solo puede editar sus propiedades
    if prop.owner_id != owner.id:
        return HttpResponseForbidden("You cannot edit a property that is not yours.")

    if request.method == "POST":
        form = PropertyForm(request.POST, request.FILES, instance=prop)
        if form.is_valid():
            form.save()
            messages.success(request, "Property updated successfully.")
            return redirect("properties:list_properties")
    else:
        form = PropertyForm(instance=prop)

    return render(request, "properties/edit.html", {"form": form, "property": prop})

# List Properties
def list_properties(request):
    qs = Property.objects.available().select_related('owner__user')

    q = request.GET.get('q', '').strip()
    city = request.GET.get('city', '').strip()
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    rooms = request.GET.get('rooms', '').strip()
    bathrooms = request.GET.get('bathrooms', '').strip()
    capacity = request.GET.get('capacity', '').strip()
    listing_type = request.GET.get('listing_type', '').strip()
    state = request.GET.get('state', '').strip()

    if q:
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(address__icontains=q) |
            Q(city__icontains=q) |
            Q(owner__user__first_name__icontains=q) |
            Q(owner__user__last_name__icontains=q) |
            Q(rooms__icontains=q) |
            Q(bathrooms__icontains=q) |
            Q(capacity__icontains=q) |
            Q(price__icontains=q)
        )

    if city:
        qs = qs.filter(
            Q(city__icontains=city) |
            Q(address__icontains=city)
        )

    if listing_type:
        qs = qs.filter(listing_type=listing_type)

    if state:
        qs = qs.filter(state=state)

    if rooms:
        try:
            qs = qs.filter(rooms=int(rooms))
        except (ValueError, TypeError):
            pass

    if bathrooms:
        try:
            qs = qs.filter(bathrooms=int(bathrooms))
        except (ValueError, TypeError):
            pass

    if capacity:
        try:
            qs = qs.filter(capacity__gte=int(capacity))
        except (ValueError, TypeError):
            pass

    if min_price:
        try:
            qs = qs.filter(price__gte=float(min_price))
        except (ValueError, TypeError):
            pass

    if max_price:
        try:
            qs = qs.filter(price__lte=float(max_price))
        except (ValueError, TypeError):
            pass

    paginator = Paginator(qs, 20)
    page = request.GET.get('page')
    properties = paginator.get_page(page)

    context = {
        'properties': properties,
        'filters': {
            'q': q,
            'city': city,
            'min_price': min_price,
            'max_price': max_price,
            'rooms': rooms,
            'bathrooms': bathrooms,
            'capacity': capacity,
            'listing_type': listing_type,
            'state': state,
        }
    }

    return render(request, 'properties/list.html', context)


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
