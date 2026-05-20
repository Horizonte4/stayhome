import requests
from django.conf import settings


def get_products():
    """Obtiene la lista de productos desde la API externa."""
    url = getattr(settings, "PRODUCT_API_URL", "")
    if not url:
        return []
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict):
            return next(iter(data.values()), [])
        return data
    except requests.RequestException as e:
        print(f"Error: {e}")
        return []
