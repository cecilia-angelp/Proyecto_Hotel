from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Habitacion


@login_required(login_url='/ingreso/')
def inicio(request):
    habitaciones = Habitacion.objects.all().order_by("numero")
    return render(request, 'habitaciones/inicio.html', {'habitaciones': habitaciones})

@login_required(login_url='/ingreso/')
def lista_habitaciones(request):
    habitaciones = Habitacion.objects.all().order_by("numero")
    return render(request, 'habitaciones/lista.html', {'habitaciones': habitaciones})

@login_required(login_url='/ingreso/')
def crear_habitacion(request):
    
    return render(request, 'habitaciones/crear.html')

@login_required(login_url='/ingreso/')
def editar_habitacion(request, pk):
   
    return render(request, 'habitaciones/editar.html')

@login_required(login_url='/ingreso/')
def eliminar_habitacion(request, pk):
    
    return render(request, 'habitaciones/eliminar.html')