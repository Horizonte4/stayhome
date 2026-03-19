from properties.models import Property
from django.shortcuts import render


# HOME
def home(request):
    properties = Property.objects.available()
    return render(request, "home.html", {'properties': properties})
