from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .validators import (
    normalizar_rut,
    normalizar_telefono,
    validar_nombre_persona,
    validar_rut,
    validar_telefono,
    validar_tipo,
)


# Modelo Habitacion
class Habitacion(models.Model):
    numero = models.IntegerField(
        unique=True, validators=[MinValueValidator(1), MaxValueValidator(9999)],
        verbose_name="Número de Habitación"
    )
    tipo = models.CharField(
        max_length=30, validators=[validar_tipo],
        verbose_name="Tipo de Habitación"
    )
    precio = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(9999999)],
        verbose_name="Precio por Noche"
    )
    disponible = models.BooleanField(default=True, verbose_name="¿Está Disponible?")

    def __str__(self):
        return f"Habitación {self.numero}"

    class Meta:
        ordering = ["numero"]
        verbose_name = "Habitación"
        verbose_name_plural = "Habitaciones"


# Modelo Huesped
class Huesped(models.Model):
    nombre = models.CharField(max_length=40, validators=[validar_nombre_persona], verbose_name="Nombre")
    apellido = models.CharField(max_length=40, validators=[validar_nombre_persona], verbose_name="Apellido")
    rut = models.CharField(max_length=10, unique=True, validators=[validar_rut], verbose_name="RUT")
    email = models.EmailField(max_length=60, verbose_name="Correo electrónico")
    telefono = models.CharField(max_length=14, validators=[validar_telefono], verbose_name="Teléfono")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["apellido", "nombre"]
        verbose_name = "Huésped"
        verbose_name_plural = "Huéspedes"

    # normalizar datos
    def save(self, *args, **kwargs):
        self.rut = normalizar_rut(self.rut)
        self.telefono = normalizar_telefono(self.telefono)
        super().save(*args, **kwargs)

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    @property
    def rut_formateado(self):
        cuerpo, _, dv = self.rut.partition("-")
        con_puntos = f"{int(cuerpo):,}".replace(",", ".") if cuerpo.isdigit() else cuerpo
        return f"{con_puntos}-{dv}"

    def __str__(self):
        return f"{self.nombre_completo} ({self.rut_formateado})"


# Modelo Reserva
class Reserva(models.Model):
    PENDIENTE, CONFIRMADA, EN_CURSO, FINALIZADA, CANCELADA = (
        "pendiente", "confirmada", "en_curso", "finalizada", "cancelada",
    )
    # estados
    ESTADOS = [
        (PENDIENTE, "Pendiente"),
        (CONFIRMADA, "Confirmada"),
        (EN_CURSO, "En curso (check-in)"),
        (FINALIZADA, "Finalizada (check-out)"),
        (CANCELADA, "Cancelada"),
    ]
    # transiciones permitidas
    TRANSICIONES = {
        PENDIENTE: [CONFIRMADA, CANCELADA],
        CONFIRMADA: [EN_CURSO, CANCELADA],
        EN_CURSO: [FINALIZADA],
        FINALIZADA: [],
        CANCELADA: [],
    }
    # estados que ocupan la habitacion
    ACTIVOS = [PENDIENTE, CONFIRMADA, EN_CURSO]
    MAX_NOCHES = 30
    MAX_ANTICIPACION_DIAS = 730

    habitacion = models.ForeignKey(Habitacion, on_delete=models.PROTECT, related_name="reservas", verbose_name="Habitación")
    huesped = models.ForeignKey(Huesped, on_delete=models.PROTECT, related_name="reservas", verbose_name="Huésped")
    fecha_entrada = models.DateField(verbose_name="Fecha de entrada")
    fecha_salida = models.DateField(verbose_name="Fecha de salida")
    personas = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(6)], verbose_name="Cantidad de personas"
    )
    estado = models.CharField(max_length=12, choices=ESTADOS, default=PENDIENTE, verbose_name="Estado")
    observaciones = models.CharField(max_length=200, blank=True, default="", verbose_name="Observaciones")
    total = models.PositiveIntegerField(default=0, editable=False, verbose_name="Total")
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_entrada", "-id"]
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"

    @property
    def noches(self):
        if self.fecha_entrada and self.fecha_salida:
            return (self.fecha_salida - self.fecha_entrada).days
        return 0

    def puede_pasar_a(self, nuevo):
        return nuevo == self.estado or nuevo in self.TRANSICIONES.get(self.estado, [])

    # validaciones
    def clean(self):
        errores = {}
        if self.fecha_entrada and self.fecha_salida:
            if self.fecha_salida <= self.fecha_entrada:
                errores["fecha_salida"] = "La fecha de salida debe ser posterior a la de entrada."
            elif self.noches > self.MAX_NOCHES:
                errores["fecha_salida"] = f"Una reserva no puede superar {self.MAX_NOCHES} noches."
            if self.fecha_entrada > date.today() + timedelta(days=self.MAX_ANTICIPACION_DIAS):
                errores["fecha_entrada"] = "La fecha de entrada no puede superar los 2 años desde hoy."
            elif self.pk is None and self.fecha_entrada < date.today():
                errores["fecha_entrada"] = "La fecha de entrada no puede estar en el pasado."
            elif self.pk is not None and self.fecha_entrada < date.today():
                original = Reserva.objects.filter(pk=self.pk).values("fecha_entrada").first()
                if original and original["fecha_entrada"] != self.fecha_entrada:
                    errores["fecha_entrada"] = "La fecha de entrada no puede estar en el pasado."

        if self.habitacion_id and self.estado in self.ACTIVOS:
            if not self.habitacion.disponible and (self.pk is None or self._cambia_habitacion()):
                errores["habitacion"] = "Esa habitación está marcada como no disponible."
            if self.fecha_entrada and self.fecha_salida and self.fecha_salida > self.fecha_entrada:
                choques = Reserva.objects.filter(
                    habitacion_id=self.habitacion_id,
                    estado__in=self.ACTIVOS,
                    fecha_entrada__lt=self.fecha_salida,
                    fecha_salida__gt=self.fecha_entrada,
                )
                if self.pk:
                    choques = choques.exclude(pk=self.pk)
                if choques.exists():
                    errores["habitacion"] = "La habitación ya está reservada en esas fechas."

        if self.pk:
            anterior = Reserva.objects.filter(pk=self.pk).values("estado").first()
            if anterior and not Reserva(estado=anterior["estado"]).puede_pasar_a(self.estado):
                errores["estado"] = (
                    f"No se puede pasar de «{dict(self.ESTADOS)[anterior['estado']]}» "
                    f"a «{dict(self.ESTADOS)[self.estado]}»."
                )
        if errores:
            raise ValidationError(errores)

    def _cambia_habitacion(self):
        original = Reserva.objects.filter(pk=self.pk).values("habitacion_id").first()
        return bool(original) and original["habitacion_id"] != self.habitacion_id

    # calcular total
    def save(self, *args, **kwargs):
        if self.habitacion_id and self.noches > 0:
            self.total = self.noches * self.habitacion.precio
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reserva #{self.pk} · Hab. {self.habitacion.numero} · {self.huesped.nombre_completo}"
