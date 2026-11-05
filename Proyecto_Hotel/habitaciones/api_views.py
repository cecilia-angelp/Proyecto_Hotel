from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from django.db.models import ProtectedError

from .models import Habitacion, Huesped, Reserva
from .serializers import HabitacionSerializer, HuespedSerializer, ReservaSerializer


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def api_login(request):
    """Entrega un token al validar usuario y contraseña."""
    username = str(request.data.get("username", "")).strip()
    password = request.data.get("password", "")
    if not username or not password:
        return Response(
            {"error": "Debes enviar username y password."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if len(username) > 30 or len(str(password)) > 30:
        return Response(
            {"error": "Usuario o contraseña con formato inválido."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response(
            {"error": "Usuario o contraseña incorrectos."},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    if not user.is_active:
        return Response({"error": "La cuenta está desactivada."}, status=status.HTTP_403_FORBIDDEN)
    token, _ = Token.objects.get_or_create(user=user)
    return Response(
        {"token": token.key, "user": user.username, "detail": "Autenticación correcta."},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_logout(request):
    request.user.auth_token.delete()
    return Response({"detail": "Sesión API cerrada correctamente."}, status=status.HTTP_200_OK)


@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_habitaciones(request):
    if request.method == "GET":
        habitaciones = Habitacion.objects.all().order_by("numero")
        return Response(HabitacionSerializer(habitaciones, many=True).data)

    serializer = HabitacionSerializer(data=request.data)
    if serializer.is_valid():
        habitacion = serializer.save()
        return Response(HabitacionSerializer(habitacion).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "DELETE"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_habitacion_detalle(request, pk):
    try:
        habitacion = Habitacion.objects.get(pk=pk)
    except Habitacion.DoesNotExist:
        return Response({"error": "La habitación no existe."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(HabitacionSerializer(habitacion).data)

    if request.method == "PUT":
        serializer = HabitacionSerializer(habitacion, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        habitacion.delete()
    except ProtectedError:
        return Response(
            {"error": "No se puede eliminar: la habitación tiene reservas asociadas."},
            status=status.HTTP_409_CONFLICT,
        )
    return Response(status=status.HTTP_204_NO_CONTENT)


def _crud_coleccion(request, modelo, serializer_cls, orden):
    if request.method == "GET":
        return Response(serializer_cls(modelo.objects.all().order_by(*orden), many=True).data)
    serializer = serializer_cls(data=request.data)
    if serializer.is_valid():
        objeto = serializer.save()
        return Response(serializer_cls(objeto).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def _crud_detalle(request, pk, modelo, serializer_cls, nombre, error_borrado):
    try:
        objeto = modelo.objects.get(pk=pk)
    except modelo.DoesNotExist:
        return Response({"error": f"{nombre} no existe."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(serializer_cls(objeto).data)

    if request.method == "PUT":
        serializer = serializer_cls(objeto, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        objeto.delete()
    except ProtectedError:
        return Response({"error": error_borrado}, status=status.HTTP_409_CONFLICT)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_huespedes(request):
    return _crud_coleccion(request, Huesped, HuespedSerializer, ["apellido", "nombre"])


@api_view(["GET", "PUT", "DELETE"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_huesped_detalle(request, pk):
    return _crud_detalle(request, pk, Huesped, HuespedSerializer, "El huésped",
                         "No se puede eliminar: el huésped tiene reservas asociadas.")


@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_reservas(request):
    return _crud_coleccion(request, Reserva, ReservaSerializer, ["-fecha_entrada", "-id"])


@api_view(["GET", "PUT", "DELETE"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_reserva_detalle(request, pk):
    if request.method == "DELETE":
        reserva = Reserva.objects.filter(pk=pk).first()
        if reserva and reserva.estado == Reserva.EN_CURSO:
            return Response(
                {"error": "No se puede eliminar una reserva en curso. Finalízala primero."},
                status=status.HTTP_409_CONFLICT,
            )
    return _crud_detalle(request, pk, Reserva, ReservaSerializer, "La reserva",
                         "No se puede eliminar la reserva.")
