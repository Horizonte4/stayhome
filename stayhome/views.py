from properties.models import Property
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _


# HOME
def home(request):
    properties = Property.objects.available()
    return render(request, "home.html", {'properties': properties})
