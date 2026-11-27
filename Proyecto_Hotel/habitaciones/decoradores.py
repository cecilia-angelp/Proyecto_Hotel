"""Decorador propio para proteger las vistas HTML."""
import secrets
from functools import wraps

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

from .autenticacion import borrar_cookies, poner_cookie_access
from .models import Sesion
from .tokens import renovar_access


def _sesion_valida(request):
    """Devuelve la Sesion si la cookie de sesion y el refresh de la cookie son validos."""
    sid = request.session.get("sesion_id")
    refresh = request.COOKIES.get(settings.COOKIE_REFRESH, "")
    if not sid or not refresh:
        return None
    sesion = Sesion.objects.select_related("usuario").filter(pk=sid, activa=True).first()
    if sesion is None or sesion.refresh_expira <= timezone.now() or not sesion.usuario.is_active:
        return None
    if not secrets.compare_digest(refresh, sesion.refresh_token):
        return None
    return sesion


def sesion_requerida(vista):
    """Solo deja pasar a quien tiene una sesion activa; si no, redirige al login."""
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        sesion = _sesion_valida(request)
        if sesion is None:
            request.session.flush()
            respuesta = redirect(f"{reverse('login')}?expirada=1")
            borrar_cookies(respuesta)
            return respuesta

        # Si el Access ya expiro, se renueva con el Refresh antes de mostrar la pagina
        renovado = False
        if sesion.access_expira <= timezone.now():
            renovar_access(sesion)
            renovado = True

        request.sesion = sesion
        request.user = sesion.usuario
        respuesta = vista(request, *args, **kwargs)
        if renovado or request.COOKIES.get(settings.COOKIE_ACCESS) != sesion.access_token:
            poner_cookie_access(respuesta, sesion)
        return respuesta
    return envoltura
