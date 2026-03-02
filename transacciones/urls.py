from django.urls import path
from .views import request_lease

app_name = 'transacciones'

urlpatterns = [
    path('request-lease/<int:propiedad_id>/', request_lease, name='request_lease'),
]