from datetime import date

from django.contrib import messages
from django.db.models import ProtectedError
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache

from .forms import HabitacionForm, HuespedForm, ReservaForm, lista_de_errores
from .models import Habitacion, Huesped, Reserva


@never_cache
@login_required
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


@never_cache
@login_required
def lista_habitaciones(request):
    habitaciones = Habitacion.objects.all().order_by("numero")
    return render(request, "habitaciones/lista.html", {"habitaciones": habitaciones})


@never_cache
@login_required
def crear_habitacion(request):
    if request.method == "POST":
        form = HabitacionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "La habitación fue registrada correctamente.")
            return redirect("lista_habitaciones")
        context = {"errores": lista_de_errores(form), "datos": request.POST}
        return render(request, "habitaciones/crear.html", context)

    return render(request, "habitaciones/crear.html")


@never_cache
@login_required
def editar_habitacion(request, pk):
    habitacion = get_object_or_404(Habitacion, pk=pk)

    if request.method == "POST":
        form = HabitacionForm(request.POST, instance=habitacion)
        if form.is_valid():
            form.save()
            messages.success(request, "La habitación fue modificada correctamente.")
            return redirect("lista_habitaciones")
        # Importante: tras un form inválido, "habitacion" puede traer valores sin guardar.
        habitacion = get_object_or_404(Habitacion, pk=pk)
        context = {
            "habitacion": habitacion,
            "errores": lista_de_errores(form),
            "datos": request.POST,
        }
        return render(request, "habitaciones/editar.html", context)

    return render(request, "habitaciones/editar.html", {"habitacion": habitacion})


@never_cache
@login_required
def eliminar_habitacion(request, pk):
    habitacion = get_object_or_404(Habitacion, pk=pk)

    if request.method == "POST":
        numero = habitacion.numero
        try:
            habitacion.delete()
        except ProtectedError:
            messages.error(
                request,
                f"No se puede eliminar la habitación {numero}: tiene reservas asociadas. "
                "Elimina o cancela primero esas reservas.",
            )
            return redirect("lista_habitaciones")
        messages.success(request, f"La habitación {numero} fue eliminada correctamente.")
        return redirect("lista_habitaciones")

    return render(request, "habitaciones/eliminar.html", {"habitacion": habitacion})


# ----------------------------- HUÉSPEDES -----------------------------

@never_cache
@login_required
def lista_huespedes(request):
    return render(request, "habitaciones/huesped_lista.html", {"huespedes": Huesped.objects.all()})


@never_cache
@login_required
def crear_huesped(request):
    if request.method == "POST":
        form = HuespedForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "El huésped fue registrado correctamente.")
            return redirect("lista_huespedes")
        return render(request, "habitaciones/huesped_form.html",
                      {"errores": lista_de_errores(form), "datos": request.POST})
    return render(request, "habitaciones/huesped_form.html")


@never_cache
@login_required
def editar_huesped(request, pk):
    huesped = get_object_or_404(Huesped, pk=pk)
    if request.method == "POST":
        form = HuespedForm(request.POST, instance=huesped)
        if form.is_valid():
            form.save()
            messages.success(request, "El huésped fue modificado correctamente.")
            return redirect("lista_huespedes")
        huesped = get_object_or_404(Huesped, pk=pk)
        return render(request, "habitaciones/huesped_form.html",
                      {"huesped": huesped, "errores": lista_de_errores(form), "datos": request.POST})
    return render(request, "habitaciones/huesped_form.html", {"huesped": huesped})


@never_cache
@login_required
def eliminar_huesped(request, pk):
    huesped = get_object_or_404(Huesped, pk=pk)
    if request.method == "POST":
        nombre = huesped.nombre_completo
        try:
            huesped.delete()
        except ProtectedError:
            messages.error(
                request,
                f"No se puede eliminar a {nombre}: tiene reservas asociadas. "
                "Elimina primero esas reservas.",
            )
            return redirect("lista_huespedes")
        messages.success(request, f"El huésped {nombre} fue eliminado correctamente.")
        return redirect("lista_huespedes")
    return render(request, "habitaciones/huesped_eliminar.html", {"huesped": huesped})


# ----------------------------- RESERVAS -----------------------------

def _contexto_reserva(form, reserva=None, datos=None):
    return {
        "form": form,
        "reserva": reserva,
        "errores": lista_de_errores(form) if form.is_bound else [],
        "hoy": date.today().isoformat(),
        "hay_huespedes": Huesped.objects.exists(),
        "hay_habitaciones": Habitacion.objects.filter(disponible=True).exists(),
    }


@never_cache
@login_required
def lista_reservas(request):
    reservas = Reserva.objects.select_related("habitacion", "huesped")
    return render(request, "habitaciones/reserva_lista.html", {"reservas": reservas})


@never_cache
@login_required
def crear_reserva(request):
    if request.method == "POST":
        form = ReservaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "La reserva fue registrada correctamente.")
            return redirect("lista_reservas")
        return render(request, "habitaciones/reserva_form.html", _contexto_reserva(form))
    return render(request, "habitaciones/reserva_form.html", _contexto_reserva(ReservaForm()))


@never_cache
@login_required
def editar_reserva(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk)
    if reserva.estado in (Reserva.FINALIZADA, Reserva.CANCELADA):
        messages.error(request, "Una reserva finalizada o cancelada ya no se puede modificar.")
        return redirect("lista_reservas")
    if request.method == "POST":
        form = ReservaForm(request.POST, instance=reserva)
        if form.is_valid():
            form.save()
            messages.success(request, "La reserva fue modificada correctamente.")
            return redirect("lista_reservas")
        reserva = get_object_or_404(Reserva, pk=pk)
        return render(request, "habitaciones/reserva_form.html", _contexto_reserva(form, reserva))
    return render(request, "habitaciones/reserva_form.html",
                  _contexto_reserva(ReservaForm(instance=reserva), reserva))


@never_cache
@login_required
def eliminar_reserva(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk)
    if reserva.estado == Reserva.EN_CURSO:
        messages.error(request, "No se puede eliminar una reserva en curso. Finalízala primero.")
        return redirect("lista_reservas")
    if request.method == "POST":
        numero = reserva.pk
        reserva.delete()
        messages.success(request, f"La reserva #{numero} fue eliminada correctamente.")
        return redirect("lista_reservas")
    return render(request, "habitaciones/reserva_eliminar.html", {"reserva": reserva})
