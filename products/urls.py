from django.urls import path
from . import views

urlpatterns = [
    path("", views.stayhome_api, name="stayhome_api"),
]
