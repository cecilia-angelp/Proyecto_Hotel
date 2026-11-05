"""Validaciones reutilizables (las usan modelos, formularios web y API)."""
import re

from django.core.exceptions import ValidationError

# Letras (con tildes, ñ, ü), espacios, apóstrofe y guion. Sin números ni símbolos raros.
_PATRON_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?:[ '\-][A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)*$")
_PATRON_TIPO = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+(?:[ \-][A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+)*$")
_PATRON_RUT = re.compile(r"^\d{7,8}-[\dK]$")


def validar_tipo(valor):
    """Tipo de habitación: letras, números, espacios y guiones (mín. 3 letras/números)."""
    valor = (valor or "").strip()
    if len(valor) < 3:
        raise ValidationError("El tipo de habitación debe tener al menos 3 caracteres.")
    if not _PATRON_TIPO.match(valor):
        raise ValidationError("El tipo solo puede llevar letras, números, espacios y guiones.")


def validar_nombre_persona(valor):
    """Nombres y apellidos: solo letras (con tildes), espacios, guion y apóstrofe."""
    valor = (valor or "").strip()
    if len(valor) < 2:
        raise ValidationError("Debe tener al menos 2 caracteres.")
    if not _PATRON_NOMBRE.match(valor):
        raise ValidationError("Solo puede contener letras (sin números ni símbolos).")


def normalizar_rut(valor):
    """'12.159.159-8' / '12159159-8' / '121591598' -> '12159159-8' (mayúscula en K)."""
    limpio = re.sub(r"[.\s]", "", str(valor or "")).upper()
    if "-" not in limpio and len(limpio) >= 2:
        limpio = f"{limpio[:-1]}-{limpio[-1]}"
    return limpio


def validar_rut(valor):
    """Solo FORMATO (7-8 dígitos, guion y dígito verificador 0-9 o K).

    A propósito no calcula el dígito verificador: se aceptan RUT de prueba.
    """
    if not _PATRON_RUT.match(normalizar_rut(valor)):
        raise ValidationError("El RUT no tiene un formato válido. Ejemplo: 12.345.678-9")


def validar_telefono(valor):
    """Teléfono: +56 opcional y luego 9 dígitos (celular chileno 9XXXXXXXX) u 8-9 dígitos."""
    limpio = re.sub(r"[\s\-]", "", str(valor or ""))
    if not re.match(r"^(\+?56)?\d{8,9}$", limpio):
        raise ValidationError("El teléfono debe tener 9 dígitos. Ejemplo: 912345678")


def normalizar_telefono(valor):
    return re.sub(r"[\s\-]", "", str(valor or ""))
