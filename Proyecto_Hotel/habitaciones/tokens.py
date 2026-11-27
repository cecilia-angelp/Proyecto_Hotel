"""Creacion, validacion y renovacion de tokens JWT (PyJWT) y registro de sesiones."""
import uuid
from datetime import timedelta

import jwt
from django.conf import settings
from django.utils import timezone

from .models import Sesion

ALGORITMO = "HS256"


# Errores de token
class ErrorToken(Exception):
    """Error base. El mensaje se devuelve tal cual al cliente."""


class TokenAusente(ErrorToken):
    pass


class TokenInvalido(ErrorToken):
    pass


class TokenExpirado(ErrorToken):
    pass


# Crear un token firmado
def _crear(usuario, sesion_id, tipo, minutos):
    ahora = timezone.now()
    expira = ahora + timedelta(minutes=minutos)
    jti = str(uuid.uuid4())
    carga = {
        "sub": str(usuario.pk),
        "username": usuario.username,
        "tipo": tipo,          # "access" o "refresh"
        "jti": jti,            # identificador unico del token
        "sid": sesion_id,      # id de la fila en la tabla Sesion
        "iat": ahora,
        "exp": expira,
    }
    token = jwt.encode(carga, settings.SECRET_KEY, algorithm=ALGORITMO)
    return token, jti, expira


# Leer y validar un token
def decodificar(token, tipo, verificar_exp=True):
    if not token:
        raise TokenAusente("Token requerido.")
    try:
        carga = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[ALGORITMO],
            options={"verify_exp": verificar_exp, "require": ["exp", "jti", "sid", "tipo"]},
        )
    except jwt.ExpiredSignatureError:
        raise TokenExpirado("El token expiró." if tipo == "access" else "El refresh token expiró.")
    except jwt.PyJWTError:
        raise TokenInvalido("Token inválido.")
    if carga.get("tipo") != tipo:
        raise TokenInvalido(f"Token inválido: se esperaba un {tipo} token.")
    return carga


# Sesiones
def _datos_cliente(request):
    ip = request.META.get("REMOTE_ADDR") or None
    navegador = (request.META.get("HTTP_USER_AGENT") or "")[:200]
    return ip, navegador


def abrir_sesion(usuario, request):
    """Crea la fila Sesion y los dos tokens (Access y Refresh)."""
    ip, navegador = _datos_cliente(request)
    ahora = timezone.now()
    sesion = Sesion.objects.create(
        usuario=usuario, jti_access="-", jti_refresh="-", access_token="-", refresh_token="-",
        access_expira=ahora, refresh_expira=ahora, ip=ip, navegador=navegador,
    )
    sesion.access_token, sesion.jti_access, sesion.access_expira = _crear(
        usuario, sesion.pk, "access", settings.JWT_ACCESS_MINUTOS)
    sesion.refresh_token, sesion.jti_refresh, sesion.refresh_expira = _crear(
        usuario, sesion.pk, "refresh", settings.JWT_REFRESH_MINUTOS)
    sesion.save()
    return sesion


def renovar_access(sesion):
    """Genera un Access nuevo y lo guarda en la base de datos."""
    sesion.access_token, sesion.jti_access, sesion.access_expira = _crear(
        sesion.usuario, sesion.pk, "access", settings.JWT_ACCESS_MINUTOS)
    sesion.save(update_fields=["access_token", "jti_access", "access_expira", "actualizada"])
    return sesion


def cerrar_sesion(sesion):
    """Revoca la sesion: sus tokens dejan de servir aunque no hayan expirado."""
    sesion.activa = False
    sesion.cerrada_en = timezone.now()
    sesion.save(update_fields=["activa", "cerrada_en", "actualizada"])
