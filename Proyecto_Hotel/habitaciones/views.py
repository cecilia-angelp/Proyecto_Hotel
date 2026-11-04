from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required

from .models import Habitacion

@login_required(login_url='/ingreso/')
def inicio(request):
    habitaciones = Habitacion.objects.all().order_by("numero")
    disponibles = Habitacion.objects.filter(disponible=True).count()
    ocupadas = Habitacion.objects.filter(disponible=False).count()

    context = {
        "habitaciones": habitaciones,
        "total_habitaciones": habitaciones.count(),
        "disponibles": disponibles,
        "ocupadas": ocupadas,
    }
    return render(request, "habitaciones/inicio.html", context)

@login_required(login_url='/ingreso/')
def lista_habitaciones(request):
    habitaciones = Habitacion.objects.all().order_by("numero")
    return render(
        request,
        "habitaciones/lista.html",
        {"habitaciones": habitaciones},
    )

@login_required(login_url='/ingreso/')
def crear_habitacion(request):
    if request.method == "POST":
        numero = request.POST.get("numero", "").strip()
        tipo = request.POST.get("tipo", "").strip()
        precio = request.POST.get("precio", "").strip()
        disponible = request.POST.get("disponible") == "on"

        errores = []

        if not numero:
            errores.append("El número de habitación es obligatorio.")
        else:
            try:
                numero = int(numero)
                if numero <= 0:
                    errores.append("El número de habitación debe ser mayor que cero.")
                elif len(str(numero)) > 10:
                    errores.append("El número de habitación no puede ser tan largo.")
            except ValueError:
                errores.append("El número de habitación debe ser un número entero.")

        if not tipo:
            errores.append("El tipo de habitación es obligatorio.")
        elif len(tipo) > 30:
            errores.append("El tipo de habitación no puede superar los 30 caracteres.")

        if not precio:
            errores.append("El precio por noche es obligatorio.")
        else:
            try:
                precio = int(precio)
                if precio <= 0:
                    errores.append("El precio debe ser mayor que cero.")
                elif precio > 9999999:
                    errores.append("El precio máximo permitido es 9.999.999.")
            except ValueError:
                errores.append("El precio debe ser un número entero.")

        if not errores and Habitacion.objects.filter(numero=numero).exists():
            errores.append(f"Ya existe una habitación con el número {numero}.")

        if errores:
            context = {
                "errores": errores,
                "datos": request.POST,
            }
            return render(request, "habitaciones/crear.html", context)

        Habitacion.objects.create(
            numero=numero,
            tipo=tipo,
            precio=precio,
            disponible=disponible,
        )
        messages.success(request, "La habitación fue registrada correctamente.")
        return redirect("lista_habitaciones")

    return render(request, "habitaciones/crear.html")

@login_required(login_url='/ingreso/')
def editar_habitacion(request, pk):
    habitacion = get_object_or_404(Habitacion, pk=pk)

    if request.method == "POST":
        numero = request.POST.get("numero", "").strip()
        tipo = request.POST.get("tipo", "").strip()
        precio = request.POST.get("precio", "").strip()
        disponible = request.POST.get("disponible") == "on"

        errores = []

        if not numero:
            errores.append("El número de habitación es obligatorio.")
        else:
            try:
                numero = int(numero)
                if numero <= 0:
                    errores.append("El número de habitación debe ser mayor que cero.")
                elif len(str(numero)) > 10:
                    errores.append("El número de habitación no puede ser tan largo.")
            except ValueError:
                errores.append("El número de habitación debe ser un número entero.")

        if not tipo:
            errores.append("El tipo de habitación es obligatorio.")
        elif len(tipo) > 30:
            errores.append("El tipo de habitación no puede superar los 30 caracteres.")

        if not precio:
            errores.append("El precio por noche es obligatorio.")
        else:
            try:
                precio = int(precio)
                if precio <= 0:
                    errores.append("El precio debe ser mayor que cero.")
                elif precio > 9999999:
                    errores.append("El precio máximo permitido es 9.999.999.")
            except ValueError:
                errores.append("El precio debe ser un número entero.")

        numero_repetido = (
            Habitacion.objects.filter(numero=numero)
            .exclude(pk=habitacion.pk)
            .exists()
            if isinstance(numero, int)
            else False
        )

        if numero_repetido:
            errores.append(f"Ya existe otra habitación con el número {numero}.")

        if errores:
            context = {
                "habitacion": habitacion,
                "errores": errores,
                "datos": request.POST,
            }
            return render(request, "habitaciones/editar.html", context)

        habitacion.numero = numero
        habitacion.tipo = tipo
        habitacion.precio = precio
        habitacion.disponible = disponible
        habitacion.save()

        messages.success(request, "La habitación fue modificada correctamente.")
        return redirect("lista_habitaciones")

    return render(request, "habitaciones/editar.html", {"habitacion": habitacion})

@login_required(login_url='/ingreso/')
def eliminar_habitacion(request, pk):
    habitacion = get_object_or_404(Habitacion, pk=pk)

    if request.method == "POST":
        numero = habitacion.numero
        habitacion.delete()
        messages.success(request, f"La habitación {numero} fue eliminada correctamente.")
        return redirect("lista_habitaciones")

    return render(
        request,
        "habitaciones/eliminar.html",
        {"habitacion": habitacion},
    )