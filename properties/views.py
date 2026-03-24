from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from .forms import PropertyForm
from .models import Property
from .selectors import (
    get_property_detail,
    get_saved_property_ids,
    get_user_favorites,
    get_user_wishlist,
    list_available_properties,
)
from .services import PropertyService


def _get_property_filters(request):
    return {
        "q": request.GET.get("q", "").strip(),
        "city": request.GET.get("city", "").strip(),
        "min_price": request.GET.get("min_price", "").strip(),
        "max_price": request.GET.get("max_price", "").strip(),
        "rooms": request.GET.get("rooms", "").strip(),
        "bathrooms": request.GET.get("bathrooms", "").strip(),
        "capacity": request.GET.get("capacity", "").strip(),
        "listing_type": request.GET.get("listing_type", "").strip(),
        "state": request.GET.get("state", "").strip(),
        "check_in": request.GET.get("check_in", "").strip(),
        "check_out": request.GET.get("check_out", "").strip(),
    }


@login_required
def create_property(request):
    owner = getattr(request.user, "owner", None)
    if not owner:
        messages.error(request, "Only property owners can create properties.")
        return redirect("home")

    form = PropertyForm(
        request.POST or None,
        request.FILES or None,
        show_active_listing=False,
    )

    if request.method == "POST" and form.is_valid():
        try:
            PropertyService.create_property(
                form=form,
                owner=owner,
                availability_dates=request.POST.get("availability_dates", ""),
            )
        except ValueError as exc:
            form.add_error(None, str(exc))
            messages.error(request, "Please correct the errors below.")
        else:
            messages.success(request, "Property created successfully.")
            return redirect("properties:list_properties")

    return render(request, "properties/create.html", {"form": form})


@login_required
def edit_property(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)

    try:
        PropertyService.validate_owner_access(
            user=request.user,
            property_obj=property_obj,
        )
    except PermissionError:
        messages.error(request, "You do not have permission to edit properties.")
        return HttpResponseForbidden("Forbidden")

    form = PropertyForm(
        request.POST or None,
        request.FILES or None,
        instance=property_obj,
    )

    if request.method == "POST" and form.is_valid():
        PropertyService.update_property(form=form)
        messages.success(request, "Property updated successfully.")
        return redirect("properties:list_properties")

    context = {
        "form": form,
        "property": property_obj,
    }
    return render(request, "properties/edit.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def delete_property(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)

    try:
        PropertyService.validate_owner_access(
            user=request.user,
            property_obj=property_obj,
        )
    except PermissionError:
        messages.error(
            request,
            "You do not have permission to delete this property.",
        )
        return HttpResponseForbidden("Forbidden")

    if request.method == "POST":
        PropertyService.delete_property(property_obj=property_obj)
        messages.success(request, "Property deleted successfully.")
        return redirect("properties:list_properties")

    return render(
        request,
        "properties/delete_confirmation.html",
        {"property": property_obj},
    )


@login_required
def edit_calendar(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)

    try:
        PropertyService.validate_owner_access(
            user=request.user,
            property_obj=property_obj,
        )
    except PermissionError:
        messages.error(
            request,
            "You do not have permission to edit this calendar.",
        )
        return HttpResponseForbidden("Forbidden")

    if request.method == "POST":
        try:
            PropertyService.update_availability_calendar(
                property_obj=property_obj,
                availability_dates=request.POST.get("availability_dates", ""),
            )
        except ValueError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, "Calendar updated successfully.")
            return redirect("properties:property_detail", pk=property_obj.pk)

    context = {
        "property": property_obj,
        "blocked_dates_json": PropertyService.get_blocked_dates_json(
            property_obj=property_obj,
        ),
    }
    return render(request, "properties/edit_calendar.html", context)


def list_properties(request):
    filters = _get_property_filters(request)
    properties_qs = list_available_properties(filters=filters)

    paginator = Paginator(properties_qs, 20)
    page_number = request.GET.get("page")
    properties = paginator.get_page(page_number)

    saved_property_ids = set()
    if request.user.is_authenticated:
        saved_property_ids = get_saved_property_ids(user=request.user)

    context = {
        "properties": properties,
        "saved_property_ids": saved_property_ids,
        "filters": filters,
    }
    return render(request, "properties/list.html", context)


@login_required
@require_POST
def toggle_saved_property(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, active_listing=True)

    result = PropertyService.toggle_saved_property(
        user=request.user,
        property_obj=property_obj,
    )

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(result)

    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)

    return redirect("properties:property_detail", pk=property_obj.pk)


@login_required
def favorites_list(request):
    saved_properties = get_user_favorites(user=request.user)
    return render(
        request,
        "properties/favorites_list.html",
        {"saved_properties": saved_properties},
    )


@login_required
def wishlist_list(request):
    saved_properties = get_user_wishlist(user=request.user)
    return render(
        request,
        "properties/wishlist_list.html",
        {"saved_properties": saved_properties},
    )


def property_detail(request, pk):
    property_obj = get_property_detail(pk=pk)
    if property_obj is None:
        raise Http404("Property not found.")

    if not PropertyService.can_access_property(
        user=request.user,
        property_obj=property_obj,
    ):
        raise Http404

    context = PropertyService.build_property_detail_context(
        user=request.user,
        property_obj=property_obj,
    )
    return render(request, "properties/detail.html", context)