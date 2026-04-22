from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from properties.models import Property


# HOME
def home(request):
    properties = Property.objects.with_owner().available()
    return render(request, "home.html", {'properties': properties})
