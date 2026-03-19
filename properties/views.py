# Python
import json
from datetime import date, datetime, timedelta
from urllib import request

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from datetime import datetime

# Local apps
from .models import Property, Booking, SavedProperty
from .forms import PropertyForm
from transactions.models import Booking


def _normalize_availability_dates(raw_dates):
    raw_dates = (raw_dates or "").strip()
    if not raw_dates:
        return "", []

    parsed_dates = []
    errors = []
    for part in raw_dates.split(","):
        value = part.strip()
        if not value:
            continue
        try:
            datetime.strptime(value, "%Y-%m-%d")
            parsed_dates.append(value)
        except ValueError:
            errors.append(value)

    if errors:
        return None, errors

    return ",".join(sorted(set(parsed_dates))), []


# Crear Propiedad
@login_required
def create_property(request):
    owner = getattr(request.user, 'owner', None)
    if not owner:
        messages.error(request, 'Only property owners can create properties.')
        return redirect('home')

    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES, show_active_listing=False)
        if form.is_valid():
            blocked_dates, invalid_dates = _normalize_availability_dates(
                request.POST.get("availability_dates", "")
            )
            if invalid_dates:
                form.add_error(
                    None,
                    "Invalid blocked date format: " + ", ".join(invalid_dates)
                )
                messages.error(request, 'Please correct the errors below to save the property.')
            else:
                property = form.save(commit=False)
                property.owner = owner
                property.active_listing = True
                property.availability_dates = blocked_dates
                property.save()
                messages.success(request, 'Property created successfully.')
                return redirect('properties:list_properties')
        else:
            messages.error(request, 'Please correct the errors below to save the property.')
    else:
        form = PropertyForm(show_active_listing=False)

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


@login_required
def edit_calendar(request, pk):
    prop = get_object_or_404(Property, pk=pk)

    owner = getattr(request.user, "owner", None)
    if not owner or prop.owner_id != owner.id:
        messages.error(request, "You do not have permission to edit this calendar.")
        return HttpResponseForbidden("Forbidden")

    if request.method == "POST":
        blocked_dates, invalid_dates = _normalize_availability_dates(
            request.POST.get("availability_dates", "")
        )
        if blocked_dates == "":
            prop.availability_dates = ""  # sin fechas bloqueadas -> todo disponible
            prop.save()
            messages.success(request, "Calendario actualizado. Todos los días están disponibles.")
            return redirect("properties:property_detail", pk=prop.pk)

        if invalid_dates:
            messages.error(
                request,
                "Formato de fechas inválido: " + ", ".join(invalid_dates)
            )

        else:
            prop.availability_dates = blocked_dates
            prop.save()
            messages.success(request, "Calendario actualizado. Las fechas seleccionadas quedaron bloqueadas.")
            return redirect("properties:property_detail", pk=prop.pk)

    blocked_dates = []
    if prop.availability_dates:
        blocked_dates = [d.strip() for d in prop.availability_dates.split(",") if d.strip()]

    context = {
        "property": prop,
        "blocked_dates_json": json.dumps(blocked_dates),
    }

    return render(request, "properties/edit_calendar.html", context)


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
    check_in = request.GET.get('check_in', '').strip()
    check_out = request.GET.get('check_out', '').strip()

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

    if check_in and check_out:
        try:
            start_date = datetime.strptime(check_in, "%Y-%m-%d").date()
            end_date = datetime.strptime(check_out, "%Y-%m-%d").date()

            if start_date < end_date:
                available_ids = []

                for prop in qs:
                    blocked = get_blocked_dates(prop)
                    reserved = set(get_reserved_dates(prop))

                    is_available = True
                    current = start_date

                    while current < end_date:
                        if current in blocked or current.strftime("%Y-%m-%d") in reserved:
                            is_available = False
                            break
                        current += timedelta(days=1)

                    if is_available:
                        available_ids.append(prop.id)

                qs = qs.filter(id__in=available_ids)

        except (ValueError, TypeError):
            pass

    paginator = Paginator(qs, 20)
    page = request.GET.get('page')
    properties = paginator.get_page(page)

    saved_property_ids = set()
    if request.user.is_authenticated:
        saved_property_ids = set(
            SavedProperty.objects.filter(user=request.user)
            .values_list('property_obj_id', flat=True)
        )

    context = {
        'properties': properties,
        'saved_property_ids': saved_property_ids,
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
            'check_in': check_in,
            'check_out': check_out,
        }
    }

    return render(request, 'properties/list.html', context)


# Toggle save property
@login_required
@require_POST
def toggle_saved_property(request, pk):
    prop = get_object_or_404(Property, pk=pk, active_listing=True)

    saved_property, created = SavedProperty.objects.get_or_create(
        user=request.user,
        property_obj=prop,
    )

    if created:
        is_saved = True
        action = 'added'
    else:
        saved_property.delete()
        is_saved = False
        action = 'removed'

    category = 'wishlist' if prop.listing_type == 'sale' else 'favorites'

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'is_saved': is_saved,
            'action': action,
            'category': category,
            'property_id': prop.pk,
        })

    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)

    return redirect('properties:property_detail', pk=prop.pk)


@login_required
def favorites_list(request):
    saved_properties = (
        SavedProperty.objects
        .favorites()
        .filter(user=request.user)
    )

    return render(request, 'properties/favorites_list.html', {
        'saved_properties': saved_properties,
    })


@login_required
def wishlist_list(request):
    saved_properties = (
        SavedProperty.objects
        .wishlist()
        .filter(user=request.user)
    )

    return render(request, 'properties/wishlist_list.html', {
        'saved_properties': saved_properties,
    })


# Dias bloqueados por el owner para mostrar en el calendario de la propiedad
def get_blocked_dates(property):

    if not property.availability_dates:
        return set()

    dates = property.availability_dates.split(",")

    blocked = {
        datetime.strptime(d.strip(), "%Y-%m-%d").date()
        for d in dates if d.strip()
    }

    return blocked


# Dias bloqueados porque ya fueron aprovadas por el owner
def get_reserved_dates(property):

    bookings = Booking.objects.filter(
        property=property,
        status="approved"
    )

    reserved = set()

    for booking in bookings:

        current = booking.check_in

        while current <= booking.check_out:
            reserved.add(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)

    return list(reserved)


def property_detail(request, pk):

    property = get_object_or_404(Property, pk=pk, active_listing=True)

    today = timezone.localdate()

    start_month = today.replace(day=1)
    end_month = (start_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    blocked = get_blocked_dates(property)
    reserved = get_reserved_dates(property)

    is_saved = False
    if request.user.is_authenticated:
        is_saved = SavedProperty.objects.filter(
            user=request.user,
            property_obj=property
        ).exists()

    # -------- JSON FOR CALENDAR --------
    blocked_dates_json = json.dumps([
        d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else d
        for d in blocked
    ])

    reserved_dates_json = json.dumps(reserved)

    # -------- AVAILABILITY --------
    all_days_available = not blocked and not reserved

    # -------- DAYS FOR MONTH VIEW --------
    days = []
    current = start_month

    while current <= end_month:

        days.append({
            "date": current,
            "is_available": all_days_available or (current not in blocked and current.strftime("%Y-%m-%d") not in reserved),
            "is_today": current == today
        })

        current += timedelta(days=1)

    context = {
        "property": property,
        "is_saved": is_saved,
        "days": days,
        "month_label": today.strftime("%B %Y"),
        "blocked_dates_json": blocked_dates_json,
        "reserved_dates_json": reserved_dates_json,
        "all_days_available": all_days_available,
    }
    return render(request, "properties/detail.html", context)

