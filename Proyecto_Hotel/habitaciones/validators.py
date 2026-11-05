import re

from django.core.exceptions import ValidationError

# patrones
_PATRON_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?:[ '\-][A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)*$")
_PATRON_TIPO = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+(?:[ \-][A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+)*$")
_PATRON_RUT = re.compile(r"^\d{7,8}-[\dK]$")


# Tipo de habitacion
def validar_tipo(valor):
    valor = (valor or "").strip()
    if len(valor) < 3:
        raise ValidationError("El tipo de habitación debe tener al menos 3 caracteres.")
    if not _PATRON_TIPO.match(valor):
        raise ValidationError("El tipo solo puede llevar letras, números, espacios y guiones.")


# Nombre
def validar_nombre_persona(valor):
    valor = (valor or "").strip()
    if len(valor) < 2:
        raise ValidationError("Debe tener al menos 2 caracteres.")
    if not _PATRON_NOMBRE.match(valor):
        raise ValidationError("Solo puede contener letras (sin números ni símbolos).")


# RUT
def normalizar_rut(valor):
    limpio = re.sub(r"[.\s]", "", str(valor or "")).upper()
    if "-" not in limpio and len(limpio) >= 2:
        limpio = f"{limpio[:-1]}-{limpio[-1]}"
    return limpio


def validar_rut(valor):
    if not _PATRON_RUT.match(normalizar_rut(valor)):
        raise ValidationError("El RUT no tiene un formato válido. Ejemplo: 12.345.678-9")


# Telefono
def validar_telefono(valor):
    limpio = re.sub(r"[\s\-]", "", str(valor or ""))
    if not re.match(r"^(\+?56)?\d{8,9}$", limpio):
        raise ValidationError("El teléfono debe tener 9 dígitos. Ejemplo: 912345678")


def normalizar_telefono(valor):
    return re.sub(r"[\s\-]", "", str(valor or ""))
