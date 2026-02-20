from django.shortcuts import render, redirect
from .models import Usuario

def crear_usuario(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre_usuario')
        if nombre:  # evita guardar vacío
            Usuario.objects.create(nombre_usuario=nombre)
        return redirect('crear_usuario')

    return render(request, 'usuarios/formulario.html')
