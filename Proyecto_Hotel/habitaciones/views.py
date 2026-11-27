from datetime import date

from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from .decoradores import _sesion_valida, sesion_requerida
from .forms import ReservaForm
from .models import Habitacion, Huesped, Reserva

# Las vistas web solo muestran paginas (GET).
# Crear, editar y eliminar se hacen desde el navegador contra la API (POST, PUT y DELETE).


# Login (solo muestra el formulario; el ingreso se hace con POST /api/login/)
@never_cache
@require_GET
def ingreso(request):
    if _sesion_valida(request):
        return redirect("inicio")
    return render(request, "habitaciones/login.html", {"expirada": request.GET.get("expirada")})


# Inicio
@never_cache
@require_GET
@sesion_requerida
def inicio(request):
    habitaciones = Habitacion.objects.all().order_by("numero")
    context = {
        "habitaciones": habitaciones,
        "total_habitaciones": habitaciones.count(),
        "disponibles": Habitacion.objects.filter(disponible=True).count(),
        "ocupadas": Habitacion.objects.filter(disponible=False).count(),
    }
    return render(request, "habitaciones/inicio.html", context)


# Habitaciones
@never_cache
@require_GET
@sesion_requerida
def lista_habitaciones(request):
    habitaciones = Habitacion.objects.all().order_by("numero")
    return render(request, "habitaciones/lista.html", {"habitaciones": habitaciones})


@never_cache
@require_GET
@sesion_requerida
def crear_habitacion(request):
    return render(request, "habitaciones/crear.html")


@never_cache
@require_GET
@sesion_requerida
def editar_habitacion(request, pk):
    habitacion = get_object_or_404(Habitacion, pk=pk)
    return render(request, "habitaciones/editar.html", {"habitacion": habitacion})


@never_cache
@require_GET
@sesion_requerida
def eliminar_habitacion(request, pk):
    habitacion = get_object_or_404(Habitacion, pk=pk)
    return render(request, "habitaciones/eliminar.html", {"habitacion": habitacion})


# Huespedes
@never_cache
@require_GET
@sesion_requerida
def lista_huespedes(request):
    return render(request, "habitaciones/huesped_lista.html", {"huespedes": Huesped.objects.all()})


@never_cache
@require_GET
@sesion_requerida
def crear_huesped(request):
    return render(request, "habitaciones/huesped_form.html")


@never_cache
@require_GET
@sesion_requerida
def editar_huesped(request, pk):
    huesped = get_object_or_404(Huesped, pk=pk)
    return render(request, "habitaciones/huesped_form.html", {"huesped": huesped})


@never_cache
@require_GET
@sesion_requerida
def eliminar_huesped(request, pk):
    huesped = get_object_or_404(Huesped, pk=pk)
    return render(request, "habitaciones/huesped_eliminar.html", {"huesped": huesped})


# Reservas
def _contexto_reserva(form, reserva=None):
    return {
        "form": form,
        "reserva": reserva,
        "hoy": date.today().isoformat(),
        "hay_huespedes": Huesped.objects.exists(),
        "hay_habitaciones": Habitacion.objects.filter(disponible=True).exists(),
    }


@never_cache
@require_GET
@sesion_requerida
def lista_reservas(request):
    reservas = Reserva.objects.select_related("habitacion", "huesped")
    return render(request, "habitaciones/reserva_lista.html", {"reservas": reservas})


@never_cache
@require_GET
@sesion_requerida
def crear_reserva(request):
    return render(request, "habitaciones/reserva_form.html", _contexto_reserva(ReservaForm()))


@never_cache
@require_GET
@sesion_requerida
def editar_reserva(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk)
    return render(request, "habitaciones/reserva_form.html",
                  _contexto_reserva(ReservaForm(instance=reserva), reserva))


@never_cache
@require_GET
@sesion_requerida
def eliminar_reserva(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk)
    return render(request, "habitaciones/reserva_eliminar.html", {"reserva": reserva})
