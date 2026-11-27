"""Autenticacion JWT para la API y manejo de errores en formato JSON."""
from django.conf import settings
from django.http import Http404
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import (
    AuthenticationFailed, MethodNotAllowed, NotAuthenticated, NotFound, ParseError,
)

from .models import Sesion
from .tokens import ErrorToken, decodificar


# Cookies de sesion
def poner_cookie_access(respuesta, sesion):
    respuesta.set_cookie(
        settings.COOKIE_ACCESS, sesion.access_token,
        max_age=settings.JWT_REFRESH_MINUTOS * 60, path="/", samesite="Lax",
        httponly=False,  # el JavaScript lo lee para enviarlo en Authorization
    )


def poner_cookies(respuesta, sesion):
    poner_cookie_access(respuesta, sesion)
    respuesta.set_cookie(
        settings.COOKIE_REFRESH, sesion.refresh_token,
        max_age=settings.JWT_REFRESH_MINUTOS * 60, path="/", samesite="Lax",
        httponly=True,   # JavaScript no puede leerla
    )


def borrar_cookies(respuesta):
    respuesta.delete_cookie(settings.COOKIE_ACCESS, path="/", samesite="Lax")
    respuesta.delete_cookie(settings.COOKIE_REFRESH, path="/", samesite="Lax")


# Autenticacion de la API: Authorization: Bearer <access_token>
class JWTSesionAutenticacion(BaseAuthentication):
    def authenticate_header(self, request):
        return "Bearer"   # hace que DRF responda 401 (y no 403) sin credenciales

    def authenticate(self, request):
        cabecera = request.headers.get("Authorization", "")
        if not cabecera:
            raise AuthenticationFailed("Token requerido.")
        partes = cabecera.split()
        if len(partes) != 2 or partes[0].lower() != "bearer":
            raise AuthenticationFailed("Formato inválido. Usa: Authorization: Bearer <token>.")
        try:
            carga = decodificar(partes[1], "access")
        except ErrorToken as e:
            raise AuthenticationFailed(str(e))

        # El token debe corresponder a una sesion activa registrada en la BD
        sesion = (Sesion.objects.select_related("usuario")
                  .filter(pk=carga["sid"], activa=True, jti_access=carga["jti"]).first())
        if sesion is None or sesion.refresh_expira <= timezone.now():
            raise AuthenticationFailed("Sesión cerrada o token revocado.")
        if not sesion.usuario.is_active:
            raise AuthenticationFailed("La cuenta está desactivada.")
        return sesion.usuario, sesion


# Respuestas de error siempre como {"error": "..."}
def manejador_errores(exc, contexto):
    from rest_framework.views import exception_handler  # import tardío: evita ciclo con DRF
    respuesta = exception_handler(exc, contexto)
    if respuesta is None:
        return None
    if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
        respuesta.status_code = 401
        respuesta.data = {"error": str(exc.detail)}
    elif isinstance(exc, (NotFound, Http404)):
        respuesta.data = {"error": "Recurso no encontrado."}
    elif isinstance(exc, ParseError):
        respuesta.data = {"error": "El cuerpo debe ser un JSON válido."}
    elif isinstance(exc, MethodNotAllowed):
        respuesta.data = {"error": "Método no permitido en esta ruta."}
    else:
        respuesta.data = {"error": str(getattr(exc, "detail", exc))}
    return respuesta


# Buscar la sesion de un token (para logout y refresh)
def sesion_de_token(token, tipo, verificar_exp=True):
    carga = decodificar(token, tipo, verificar_exp=verificar_exp)
    campo = "jti_access" if tipo == "access" else "jti_refresh"
    return Sesion.objects.select_related("usuario").filter(
        pk=carga["sid"], activa=True, **{campo: carga["jti"]}).first()


