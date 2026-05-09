from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from properties.models import Property
from .services import get_products


@require_GET
def stayhome_api(request):
    """Servicio JSON para de stayhome."""
    properties = Property.objects.filter(
        listing_type__in=["short_term", "long_term"]
    ).values(
        "id",
        "title",
        "city",
    )
    data = []
    for prop in properties:
        data.append(
            {
                **prop,
                "url": request.build_absolute_uri(f"/properties/{prop['id']}/"),
            }
        )
    return JsonResponse({"properties": data}, safe=False)


@require_GET
def products_view(request):
    """Consume el servicio de la api de otro equipo."""
    items = get_products()
    print(f"Items: {items}")
    return render(request, "api/products.html", {"items": items})
