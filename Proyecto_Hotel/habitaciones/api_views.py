"""API REST con JWT. Codigos usados: 200, 201, 400, 401 y 404 (los vistos en clase)."""
from django.conf import settings
from django.contrib.auth import authenticate
from django.db.models import ProtectedError
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .autenticacion import (
    JWTSesionAutenticacion, borrar_cookies, poner_cookie_access, poner_cookies, sesion_de_token,
)
from .models import Habitacion, Huesped, Reserva, Sesion
from .serializers import HabitacionSerializer, HuespedSerializer, ReservaSerializer
from .tokens import ErrorToken, abrir_sesion, cerrar_sesion, renovar_access

SOLO_JWT = [JWTSesionAutenticacion]

# Esquemas de respuesta para Swagger
Error = inline_serializer("Error", {"error": serializers.CharField()})
ErrorValidacion = inline_serializer("ErrorValidacion", {
    "error": serializers.CharField(),
    "errores": serializers.ListField(child=serializers.CharField()),
    "detalle": serializers.DictField(),
})
Mensaje = inline_serializer("Mensaje", {"mensaje": serializers.CharField()})
CredencialesIn = inline_serializer("Credenciales", {
    "username": serializers.CharField(), "password": serializers.CharField()})
RefreshIn = inline_serializer("RefreshEntrada", {"refresh_token": serializers.CharField(required=False)})

R400 = OpenApiResponse(ErrorValidacion, description="Datos inválidos", examples=[OpenApiExample(
    "Datos inválidos", value={
        "error": "Datos inválidos.",
        "errores": ["Número de habitación: Ya existe una habitación con ese número."],
        "detalle": {"numero": ["Ya existe una habitación con ese número."]}})])
R401 = OpenApiResponse(Error, description="Token ausente, inválido, expirado o revocado", examples=[
    OpenApiExample("Sin token", value={"error": "Token requerido."}),
    OpenApiExample("Token inválido", value={"error": "Token inválido."}),
    OpenApiExample("Access vencido", value={"error": "El token expiró."}),
    OpenApiExample("Sesión cerrada", value={"error": "Sesión cerrada o token revocado."})])
R404 = OpenApiResponse(Error, description="No existe", examples=[
    OpenApiExample("No existe", value={"error": "La habitación no existe."})])
TOKEN_EJEMPLO = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ...(token de ejemplo)"


# Autenticacion
@extend_schema(
    tags=["Autenticación"], auth=[], request=CredencialesIn,
    summary="Login: genera Access y Refresh token",
    description="Valida usuario y contraseña (máximo 30 caracteres cada uno). Si son correctos crea la sesión "
                "en la base de datos y devuelve el Access token (dura poco) y el Refresh token (dura más).",
    examples=[OpenApiExample("Credenciales", value={"username": "recepcion", "password": "tu_clave"},
                             request_only=True)],
    responses={
        200: OpenApiResponse(
            inline_serializer("LoginOk", {
                "mensaje": serializers.CharField(), "access_token": serializers.CharField(),
                "refresh_token": serializers.CharField(), "usuario": serializers.CharField(),
                "sesion_id": serializers.IntegerField()}),
            description="Login correcto",
            examples=[OpenApiExample("Login correcto", value={
                "mensaje": "Login correcto.", "access_token": TOKEN_EJEMPLO, "refresh_token": TOKEN_EJEMPLO,
                "usuario": "recepcion", "sesion_id": 1})]),
        400: OpenApiResponse(Error, description="Faltan username o password",
                             examples=[OpenApiExample("Faltan datos", value={"error": "Debes enviar username y password."})]),
        401: OpenApiResponse(Error, description="Credenciales incorrectas",
                             examples=[OpenApiExample("Clave incorrecta", value={"error": "Usuario o contraseña incorrectos."})]),
    },
)
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def api_login(request):
    datos = request.data if isinstance(request.data, dict) or hasattr(request.data, "get") else {}
    username = str(datos.get("username", "")).strip()
    password = datos.get("password", "")
    if not username or not password:
        return Response({"error": "Debes enviar username y password."}, status=status.HTTP_400_BAD_REQUEST)
    if len(username) > 30 or len(str(password)) > 30:
        return Response({"error": "Usuario o contraseña con formato inválido."},
                        status=status.HTTP_400_BAD_REQUEST)
    usuario = authenticate(request, username=username, password=str(password))
    if usuario is None or not usuario.is_active:
        return Response({"error": "Usuario o contraseña incorrectos."}, status=status.HTTP_401_UNAUTHORIZED)

    sesion = abrir_sesion(usuario, request)
    # Sesion persistente de Django (cookie de 1 dia) que guarda el id de la fila Sesion
    django_request = request._request
    django_request.session.cycle_key()
    django_request.session["sesion_id"] = sesion.pk
    django_request.session.set_expiry(settings.SESSION_COOKIE_AGE)

    respuesta = Response({
        "mensaje": "Login correcto.",
        "access_token": sesion.access_token,
        "refresh_token": sesion.refresh_token,
        "usuario": usuario.username,
        "sesion_id": sesion.pk,
    }, status=status.HTTP_200_OK)
    poner_cookies(respuesta, sesion)
    return respuesta


@extend_schema(
    tags=["Autenticación"], auth=[], request=RefreshIn,
    summary="Renueva el Access token usando el Refresh token",
    description="Envía el refresh token en el cuerpo JSON (`refresh_token`) o en la cookie `refresh_token`. "
                "El Access anterior deja de servir y se usa el nuevo.",
    examples=[OpenApiExample("Refresh", value={"refresh_token": "PEGAR_AQUI_EL_REFRESH_TOKEN"}, request_only=True)],
    responses={
        200: OpenApiResponse(
            inline_serializer("RefreshOk", {
                "mensaje": serializers.CharField(), "access_token": serializers.CharField()}),
            description="Access renovado",
            examples=[OpenApiExample("Renovado", value={"mensaje": "Access token renovado.", "access_token": TOKEN_EJEMPLO})]),
        400: OpenApiResponse(Error, description="No se envió el refresh token",
                             examples=[OpenApiExample("Falta el refresh", value={"error": "Debes enviar el refresh_token."})]),
        401: OpenApiResponse(Error, description="Refresh inválido, expirado o sesión cerrada", examples=[
            OpenApiExample("Inválido", value={"error": "Token inválido."}),
            OpenApiExample("Vencido", value={"error": "El refresh token expiró."}),
            OpenApiExample("Sesión cerrada", value={"error": "Sesión cerrada o refresh token revocado."})]),
    },
)
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def api_refresh(request):
    datos = request.data if hasattr(request.data, "get") else {}
    token = datos.get("refresh_token") or datos.get("refresh") or request.COOKIES.get(settings.COOKIE_REFRESH)
    if not token:
        return Response({"error": "Debes enviar el refresh_token."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        sesion = sesion_de_token(token, "refresh")
    except ErrorToken as e:
        return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    if sesion is None or not sesion.vigente or not sesion.usuario.is_active:
        return Response({"error": "Sesión cerrada o refresh token revocado."},
                        status=status.HTTP_401_UNAUTHORIZED)
    renovar_access(sesion)
    respuesta = Response({"mensaje": "Access token renovado.", "access_token": sesion.access_token},
                         status=status.HTTP_200_OK)
    poner_cookie_access(respuesta, sesion)
    return respuesta


@extend_schema(
    tags=["Autenticación"], request=None,
    summary="Logout: revoca la sesión (los tokens dejan de servir)",
    responses={200: Mensaje, 401: R401},
)
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def api_logout(request):
    # Se acepta el Access (aunque haya expirado) o el Refresh, por cabecera o cookie
    cabecera = request.headers.get("Authorization", "").split()
    candidatos = []
    if len(cabecera) == 2 and cabecera[0].lower() == "bearer":
        candidatos.append((cabecera[1], "access"))
    candidatos.append((request.COOKIES.get(settings.COOKIE_ACCESS), "access"))
    candidatos.append((request.COOKIES.get(settings.COOKIE_REFRESH), "refresh"))
    if not any(t for t, _ in candidatos):
        return Response({"error": "Token requerido."}, status=status.HTTP_401_UNAUTHORIZED)

    sesion = None
    for token, tipo in candidatos:
        if not token:
            continue
        try:
            sesion = sesion_de_token(token, tipo, verificar_exp=False)
        except ErrorToken:
            continue
        if sesion:
            break
    if sesion is None:
        return Response({"error": "Token inválido o sesión ya cerrada."}, status=status.HTTP_401_UNAUTHORIZED)

    cerrar_sesion(sesion)
    request._request.session.flush()
    respuesta = Response({"mensaje": "Sesión cerrada correctamente."}, status=status.HTTP_200_OK)
    borrar_cookies(respuesta)
    return respuesta


# Perfil: endpoint protegido de ejemplo (200 con Access valido, 401 sin el)
@extend_schema(
    tags=["Autenticación"], summary="Perfil del usuario autenticado (endpoint protegido)",
    description="Sin token responde 401; con un Access válido responde 200.",
    responses={
        200: OpenApiResponse(
            inline_serializer("Perfil", {"usuario": serializers.CharField(), "email": serializers.CharField(),
                                         "sesion_id": serializers.IntegerField(),
                                         "access_expira": serializers.DateTimeField(),
                                         "refresh_expira": serializers.DateTimeField()}),
            description="Datos del usuario",
            examples=[OpenApiExample("Perfil", value={
                "usuario": "recepcion", "email": "", "sesion_id": 1,
                "access_expira": "2026-11-25T21:08:35Z", "refresh_expira": "2026-11-26T21:03:35Z"})]),
        401: R401,
    },
)
@api_view(["GET"])
@authentication_classes(SOLO_JWT)
@permission_classes([IsAuthenticated])
def api_perfil(request):
    sesion = request.auth
    return Response({"usuario": request.user.username, "email": request.user.email,
                     "sesion_id": sesion.pk, "access_expira": sesion.access_expira,
                     "refresh_expira": sesion.refresh_expira}, status=status.HTTP_200_OK)


# Sesiones (administracion)
_CAMPOS_SESION = {
    "id": serializers.IntegerField(), "usuario": serializers.CharField(),
    "jti_access": serializers.CharField(), "jti_refresh": serializers.CharField(),
    "creada": serializers.DateTimeField(), "access_expira": serializers.DateTimeField(),
    "refresh_expira": serializers.DateTimeField(), "activa": serializers.BooleanField(),
    "ip": serializers.CharField(), "navegador": serializers.CharField(),
}
SesionOut = inline_serializer("SesionOut", _CAMPOS_SESION, many=True)


def _sesion_a_dict(s):
    return {
        "id": s.pk, "usuario": s.usuario.username, "jti_access": s.jti_access,
        "jti_refresh": s.jti_refresh, "creada": s.creada, "access_expira": s.access_expira,
        "refresh_expira": s.refresh_expira, "activa": s.vigente, "ip": s.ip,
        "navegador": s.navegador,
    }


@extend_schema(tags=["Sesiones"], summary="Lista las sesiones del usuario",
               responses={200: SesionOut, 401: R401})
@api_view(["GET"])
@authentication_classes(SOLO_JWT)
@permission_classes([IsAuthenticated])
def api_sesiones(request):
    sesiones = Sesion.objects.filter(usuario=request.user).select_related("usuario")[:50]
    return Response([_sesion_a_dict(s) for s in sesiones], status=status.HTTP_200_OK)


@extend_schema(tags=["Sesiones"], summary="Revoca una sesión del usuario",
               responses={200: Mensaje, 401: R401, 404: R404})
@api_view(["DELETE"])
@authentication_classes(SOLO_JWT)
@permission_classes([IsAuthenticated])
def api_sesion_detalle(request, pk):
    sesion = Sesion.objects.filter(pk=pk, usuario=request.user).first()
    if sesion is None:
        return Response({"error": "La sesión no existe."}, status=status.HTTP_404_NOT_FOUND)
    cerrar_sesion(sesion)
    return Response({"mensaje": "Sesión revocada."}, status=status.HTTP_200_OK)


# Funciones comunes del CRUD
def _errores_400(serializer):
    modelo = serializer.Meta.model
    lista = []
    for campo, mensajes in serializer.errors.items():
        if campo == "non_field_errors":
            etiqueta = ""
        else:
            try:
                etiqueta = str(modelo._meta.get_field(campo).verbose_name).capitalize() + ": "
            except Exception:
                etiqueta = campo.capitalize() + ": "
        for m in (mensajes if isinstance(mensajes, (list, tuple)) else [mensajes]):
            lista.append(f"{etiqueta}{m}")
    return Response({"error": "Datos inválidos.", "errores": lista, "detalle": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST)


def _coleccion(request, modelo, serializer_cls, orden, tipo):
    if request.method == "GET":
        return Response(serializer_cls(modelo.objects.all().order_by(*orden), many=True).data,
                        status=status.HTTP_200_OK)
    serializer = serializer_cls(data=request.data)
    if not serializer.is_valid():
        return _errores_400(serializer)
    objeto = serializer.save()
    return Response({"mensaje": f"{tipo['sust']} cread{tipo['g']} correctamente.",
                     tipo["clave"]: serializer_cls(objeto).data},
                    status=status.HTTP_201_CREATED)


def _detalle(request, pk, modelo, serializer_cls, tipo, puede_modificar=None, puede_borrar=None):
    objeto = modelo.objects.filter(pk=pk).first()
    if objeto is None:
        return Response({"error": f"{tipo['art']} no existe."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(serializer_cls(objeto).data, status=status.HTTP_200_OK)

    if request.method == "PUT":
        if puede_modificar:
            motivo = puede_modificar(objeto)
            if motivo:
                return Response({"error": motivo}, status=status.HTTP_400_BAD_REQUEST)
        serializer = serializer_cls(objeto, data=request.data)
        if not serializer.is_valid():
            return _errores_400(serializer)
        serializer.save()
        return Response({"mensaje": f"{tipo['sust']} modificad{tipo['g']} correctamente.",
                         tipo["clave"]: serializer.data},
                        status=status.HTTP_200_OK)

    # DELETE
    if puede_borrar:
        motivo = puede_borrar(objeto)
        if motivo:
            return Response({"error": motivo}, status=status.HTTP_400_BAD_REQUEST)
    try:
        objeto.delete()
    except ProtectedError:
        return Response({"error": f"No se puede eliminar: {tipo['art'].lower()} tiene reservas asociadas."},
                        status=status.HTTP_400_BAD_REQUEST)
    return Response({"mensaje": f"{tipo['sust']} eliminad{tipo['g']} correctamente."},
                    status=status.HTTP_200_OK)


HABITACION = {"sust": "Habitación", "art": "La habitación", "g": "a", "clave": "habitacion"}
HUESPED = {"sust": "Huésped", "art": "El huésped", "g": "o", "clave": "huesped"}
RESERVA = {"sust": "Reserva", "art": "La reserva", "g": "a", "clave": "reserva"}

R_BORRAR_400 = OpenApiResponse(Error, description="No se puede eliminar", examples=[
    OpenApiExample("Tiene reservas", value={"error": "No se puede eliminar: la habitación tiene reservas asociadas."})])

EJ_HAB = {"numero": 301, "tipo": "Suite", "precio": 90000, "disponible": True}
EJ_HUE = {"nombre": "Camila", "apellido": "Rojas", "rut": "11.111.111-1",
          "email": "camila@correo.cl", "telefono": "912345678"}
EJ_RES = {"habitacion": 1, "huesped": 1, "fecha_entrada": "2026-12-10", "fecha_salida": "2026-12-12",
          "personas": 2, "observaciones": "Llegada tarde"}


# Documentacion Swagger de cada pareja de rutas
def doc_coleccion(serializer_cls, etiqueta, ejemplo, creado):
    def aplicar(vista):
        vista = extend_schema(methods=["POST"], tags=[etiqueta], summary=f"Crear ({etiqueta.lower()})",
                              request=serializer_cls,
                              examples=[OpenApiExample("Datos válidos", value=ejemplo, request_only=True)],
                              responses={201: OpenApiResponse(description="Creado", examples=[
                                  OpenApiExample("Creado", value=creado)]),
                                  400: R400, 401: R401})(vista)
        return extend_schema(methods=["GET"], tags=[etiqueta], summary=f"Listar ({etiqueta.lower()})",
                             responses={200: serializer_cls(many=True), 401: R401})(vista)
    return aplicar


def doc_detalle(serializer_cls, etiqueta, ejemplo, modificado, eliminado):
    def aplicar(vista):
        vista = extend_schema(methods=["DELETE"], tags=[etiqueta], summary="Eliminar por id",
                              responses={200: OpenApiResponse(Mensaje, description="Eliminado", examples=[
                                  OpenApiExample("Eliminado", value={"mensaje": eliminado})]),
                                  400: R_BORRAR_400, 401: R401, 404: R404})(vista)
        vista = extend_schema(methods=["PUT"], tags=[etiqueta], summary="Modificar por id (envía todos los campos)",
                              request=serializer_cls,
                              examples=[OpenApiExample("Datos válidos", value=ejemplo, request_only=True)],
                              responses={200: OpenApiResponse(description="Modificado", examples=[
                                  OpenApiExample("Modificado", value=modificado)]),
                                  400: R400, 401: R401, 404: R404})(vista)
        return extend_schema(methods=["GET"], tags=[etiqueta], summary="Obtener por id",
                             responses={200: serializer_cls, 401: R401, 404: R404})(vista)
    return aplicar


# Habitaciones
@doc_coleccion(HabitacionSerializer, "Habitaciones", EJ_HAB,
               {"mensaje": "Habitación creada correctamente.", "habitacion": {"id": 1, **EJ_HAB}})
@api_view(["GET", "POST"])
@authentication_classes(SOLO_JWT)
@permission_classes([IsAuthenticated])
def api_habitaciones(request):
    return _coleccion(request, Habitacion, HabitacionSerializer, ["numero"], HABITACION)


@doc_detalle(HabitacionSerializer, "Habitaciones", EJ_HAB,
             {"mensaje": "Habitación modificada correctamente.", "habitacion": {"id": 1, **EJ_HAB}},
             "Habitación eliminada correctamente.")
@api_view(["GET", "PUT", "DELETE"])
@authentication_classes(SOLO_JWT)
@permission_classes([IsAuthenticated])
def api_habitacion_detalle(request, pk):
    return _detalle(request, pk, Habitacion, HabitacionSerializer, HABITACION)


# Huespedes
@doc_coleccion(HuespedSerializer, "Huéspedes", EJ_HUE,
               {"mensaje": "Huésped creado correctamente.", "huesped": {"id": 1, **EJ_HUE}})
@api_view(["GET", "POST"])
@authentication_classes(SOLO_JWT)
@permission_classes([IsAuthenticated])
def api_huespedes(request):
    return _coleccion(request, Huesped, HuespedSerializer, ["apellido", "nombre"], HUESPED)


@doc_detalle(HuespedSerializer, "Huéspedes", EJ_HUE,
             {"mensaje": "Huésped modificado correctamente.", "huesped": {"id": 1, **EJ_HUE}},
             "Huésped eliminado correctamente.")
@api_view(["GET", "PUT", "DELETE"])
@authentication_classes(SOLO_JWT)
@permission_classes([IsAuthenticated])
def api_huesped_detalle(request, pk):
    return _detalle(request, pk, Huesped, HuespedSerializer, HUESPED)


# Reservas
def _no_modificable(reserva):
    if reserva.estado in (Reserva.FINALIZADA, Reserva.CANCELADA):
        return "Una reserva finalizada o cancelada ya no se puede modificar."


def _no_eliminable(reserva):
    if reserva.estado == Reserva.EN_CURSO:
        return "No se puede eliminar una reserva en curso. Finalízala primero."


@doc_coleccion(ReservaSerializer, "Reservas", EJ_RES,
               {"mensaje": "Reserva creada correctamente.", "reserva": {"id": 1, **EJ_RES, "estado": "pendiente"}})
@api_view(["GET", "POST"])
@authentication_classes(SOLO_JWT)
@permission_classes([IsAuthenticated])
def api_reservas(request):
    return _coleccion(request, Reserva, ReservaSerializer, ["-fecha_entrada", "-id"], RESERVA)


@doc_detalle(ReservaSerializer, "Reservas", {**EJ_RES, "estado": "confirmada"},
             {"mensaje": "Reserva modificada correctamente.", "reserva": {"id": 1, **EJ_RES, "estado": "confirmada"}},
             "Reserva eliminada correctamente.")
@api_view(["GET", "PUT", "DELETE"])
@authentication_classes(SOLO_JWT)
@permission_classes([IsAuthenticated])
def api_reserva_detalle(request, pk):
    return _detalle(request, pk, Reserva, ReservaSerializer, RESERVA,
                    puede_modificar=_no_modificable, puede_borrar=_no_eliminable)
