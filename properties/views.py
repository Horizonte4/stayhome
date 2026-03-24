import json
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from transactions.models import Booking, Contract
from transactions.selectors import can_access_property

from .forms import PropertyForm
from .models import Property, SavedProperty
from .services import (
    build_calendar_payload,
    filter_properties_by_availability,
    normalize_availability_dates,
)


def _parse_date_range(request):
    check_in = request.GET.get("check_in", "").strip()
    check_out = request.GET.get("check_out", "").strip()

    if not check_in or not check_out:
        return None, None

    try:
        start_date = datetime.strptime(check_in, "%Y-%m-%d").date()
        end_date = datetime.strptime(check_out, "%Y-%m-%d").date()
    except ValueError:
        return None, None

    if start_date >= end_date:
        return None, None

    return start_date, end_date


@login_required
def create_property(request):
    owner = getattr(request.user, "owner", None)
    if not owner:
        messages.error(request, "Only property owners can create properties.")
        return redirect("home")

    if request.method == "POST":
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            blocked_dates, invalid_dates = normalize_availability_dates(
                request.POST.get("availability_dates", "")
            )
            if invalid_dates:
                form.add_error(
                    None,
                    "Invalid blocked date format: " + ", ".join(invalid_dates),
                )
                messages.error(
                    request,
                    "Please correct the errors below to save the property.",
                )
            else:
                property_obj = form.save(commit=False)
                property_obj.owner = owner
                property_obj.availability_dates = blocked_dates
                property_obj.save()
                messages.success(request, "Property created successfully.")
                return redirect("properties:list_properties")
        else:
            messages.error(
                request,
                "Please correct the errors below to save the property.",
            )
    else:
        form = PropertyForm()

    return render(request, "properties/create.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def delete_property(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)
    owner = getattr(request.user, "owner", None)

    if not owner:
        messages.error(request, "You do not have permission to delete properties.")
        return HttpResponseForbidden("Forbidden")

    if property_obj.owner_id != owner.id:
        return HttpResponseForbidden("You cannot delete a property that is not yours.")

    if request.method == "POST":
        property_obj.delete()
        messages.success(request, "Property deleted successfully.")
        return redirect("properties:list_properties")

    return render(
        request,
        "properties/delete_confirmation.html",
        {"property": property_obj},
    )


@login_required
def edit_property(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)
    owner = getattr(request.user, "owner", None)

    if not owner:
        messages.error(request, "You do not have permission to edit properties.")
        return HttpResponseForbidden("Forbidden")

    if property_obj.owner_id != owner.id:
        return HttpResponseForbidden("You cannot edit a property that is not yours.")

    if request.method == "POST":
        form = PropertyForm(request.POST, request.FILES, instance=property_obj)
        if form.is_valid():
            updated_property = form.save(commit=False)
            updated_property.availability_dates = property_obj.availability_dates
            updated_property.save()
            messages.success(request, "Property updated successfully.")
            return redirect("properties:list_properties")
    else:
        form = PropertyForm(instance=property_obj)

    return render(
        request,
        "properties/edit.html",
        {"form": form, "property": property_obj},
    )


@login_required
def edit_calendar(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)
    owner = getattr(request.user, "owner", None)

    if not owner or property_obj.owner_id != owner.id:
        messages.error(request, "You do not have permission to edit this calendar.")
        return HttpResponseForbidden("Forbidden")

    if request.method == "POST":
        blocked_dates, invalid_dates = normalize_availability_dates(
            request.POST.get("availability_dates", "")
        )

        if blocked_dates == "":
            property_obj.availability_dates = ""
            property_obj.save(update_fields=["availability_dates"])
            messages.success(
                request,
                "Calendar updated. All dates are available.",
            )
            return redirect("properties:property_detail", pk=property_obj.pk)

        if invalid_dates:
            messages.error(
                request,
                "Invalid date format: " + ", ".join(invalid_dates),
            )
        else:
            property_obj.availability_dates = blocked_dates
            property_obj.save(update_fields=["availability_dates"])
            messages.success(
                request,
                "Calendar updated. Selected dates are now blocked.",
            )
            return redirect("properties:property_detail", pk=property_obj.pk)

    blocked_dates = []
    if property_obj.availability_dates:
        blocked_dates = [
            value.strip()
            for value in property_obj.availability_dates.split(",")
            if value.strip()
        ]

    return render(
        request,
        "properties/edit_calendar.html",
        {
            "property": property_obj,
            "blocked_dates_json": json.dumps(blocked_dates),
        },
    )


def list_properties(request):
    start_date, end_date = _parse_date_range(request)
    queryset = Property.objects.with_owner()

    query = request.GET.get("q", "").strip()
    city = request.GET.get("city", "").strip()
    min_price = request.GET.get("min_price", "").strip()
    max_price = request.GET.get("max_price", "").strip()
    rooms = request.GET.get("rooms", "").strip()
    bathrooms = request.GET.get("bathrooms", "").strip()
    capacity = request.GET.get("capacity", "").strip()
    listing_type = request.GET.get("listing_type", "").strip()

    if query:
        queryset = queryset.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(address__icontains=query)
            | Q(city__icontains=query)
            | Q(owner__user__first_name__icontains=query)
            | Q(owner__user__last_name__icontains=query)
        )

    if city:
        queryset = queryset.filter(Q(city__icontains=city) | Q(address__icontains=city))

    if listing_type:
        queryset = queryset.filter(listing_type=listing_type)

    if rooms:
        try:
            queryset = queryset.filter(rooms=int(rooms))
        except (TypeError, ValueError):
            pass

    if bathrooms:
        try:
            queryset = queryset.filter(bathrooms=int(bathrooms))
        except (TypeError, ValueError):
            pass

    if capacity:
        try:
            queryset = queryset.filter(capacity__gte=int(capacity))
        except (TypeError, ValueError):
            pass

    if min_price:
        try:
            queryset = queryset.filter(price__gte=float(min_price))
        except (TypeError, ValueError):
            pass

    if max_price:
        try:
            queryset = queryset.filter(price__lte=float(max_price))
        except (TypeError, ValueError):
            pass

    queryset = queryset.available(start_date, end_date)
    queryset = filter_properties_by_availability(queryset, start_date, end_date)

    paginator = Paginator(queryset, 20)
    page = request.GET.get("page")
    properties = paginator.get_page(page)

    saved_property_ids = set()
    if request.user.is_authenticated:
        saved_property_ids = set(
            SavedProperty.objects.filter(user=request.user).values_list(
                "property_obj_id",
                flat=True,
            )
        )

    context = {
        "properties": properties,
        "saved_property_ids": saved_property_ids,
        "filters": {
            "q": query,
            "city": city,
            "min_price": min_price,
            "max_price": max_price,
            "rooms": rooms,
            "bathrooms": bathrooms,
            "capacity": capacity,
            "listing_type": listing_type,
            "check_in": request.GET.get("check_in", "").strip(),
            "check_out": request.GET.get("check_out", "").strip(),
        },
    }
    return render(request, "properties/list.html", context)


@login_required
@require_POST
def toggle_saved_property(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)

    if not can_access_property(request.user, property_obj):
        raise Http404

    saved_property, created = SavedProperty.objects.get_or_create(
        user=request.user,
        property_obj=property_obj,
    )

    if created:
        is_saved = True
        action = "added"
    else:
        saved_property.delete()
        is_saved = False
        action = "removed"

    category = "wishlist" if property_obj.listing_type == "sale" else "favorites"

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(
            {
                "is_saved": is_saved,
                "action": action,
                "category": category,
                "property_id": property_obj.pk,
            }
        )

    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)

    return redirect("properties:property_detail", pk=property_obj.pk)


@login_required
def favorites_list(request):
    saved_properties = SavedProperty.objects.favorites().filter(user=request.user)
    return render(
        request,
        "properties/favorites_list.html",
        {"saved_properties": saved_properties},
    )


@login_required
def wishlist_list(request):
    saved_properties = SavedProperty.objects.wishlist().filter(user=request.user)
    return render(
        request,
        "properties/wishlist_list.html",
        {"saved_properties": saved_properties},
    )


def property_detail(request, pk):
    property_obj = get_object_or_404(
        Property.objects.with_owner(),
        pk=pk,
    )

    if not can_access_property(request.user, property_obj):
        raise Http404

    calendar_payload = build_calendar_payload(property_obj)
    is_saved = False
    has_purchased_property = False
    can_contact_owner = False

    if request.user.is_authenticated:
        is_saved = SavedProperty.objects.filter(
            user=request.user,
            property_obj=property_obj,
        ).exists()
        has_purchased_property = Contract.objects.filter(
            property=property_obj,
            tenant=request.user,
            type="sale",
        ).exists()
        has_approved_booking = Booking.objects.filter(
            property=property_obj,
            user=request.user,
            status="approved",
        ).exists()
        can_contact_owner = (
            property_obj.owner is not None
            and request.user != property_obj.owner.user
            and (
                property_obj.listing_type == "sale"
                or has_approved_booking
                or has_purchased_property
            )
        )

    context = {
        "property": property_obj,
        "is_saved": is_saved,
        "availability_label": property_obj.availability_label,
        "has_sale_contract": property_obj.has_sale_contract(),
        "can_contact_owner": can_contact_owner,
        "has_purchased_property": has_purchased_property,
        **calendar_payload,
    }
    return render(request, "properties/detail.html", context)
