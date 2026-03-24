from django.shortcuts import render

from properties.models import Property


# HOME
def home(request):
    properties = Property.objects.with_owner().available()
    return render(request, "home.html", {'properties': properties})
