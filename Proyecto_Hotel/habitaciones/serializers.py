from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Habitacion, Huesped, Reserva
from .validators import (
    normalizar_rut,
    normalizar_telefono,
    validar_nombre_persona,
    validar_rut,
    validar_telefono,
    validar_tipo,
)


class HabitacionSerializer(serializers.ModelSerializer):
    numero = serializers.IntegerField(min_value=1, max_value=9999)
    tipo = serializers.CharField(min_length=3, max_length=30, trim_whitespace=True)
    precio = serializers.IntegerField(min_value=1, max_value=9999999)

    class Meta:
        model = Habitacion
        fields = ["id", "numero", "tipo", "precio", "disponible"]
        read_only_fields = ["id"]

    def validate_numero(self, value):
        qs = Habitacion.objects.filter(numero=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Ya existe una habitación con ese número.")
        return value

    def validate_tipo(self, value):
        value = " ".join(value.split())
        try:
            validar_tipo(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value


class HuespedSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(max_length=40, validators=[validar_nombre_persona])
    apellido = serializers.CharField(max_length=40, validators=[validar_nombre_persona])
    rut = serializers.CharField(max_length=12, validators=[validar_rut])
    email = serializers.EmailField(max_length=60)
    telefono = serializers.CharField(max_length=16, validators=[validar_telefono])

    class Meta:
        model = Huesped
        fields = ["id", "nombre", "apellido", "rut", "email", "telefono"]
        read_only_fields = ["id"]

    def validate_nombre(self, value):
        return " ".join(value.split())

    def validate_apellido(self, value):
        return " ".join(value.split())

    def validate_rut(self, value):
        rut = normalizar_rut(value)
        qs = Huesped.objects.filter(rut=rut)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Ya existe un huésped con ese RUT.")
        return rut

    def validate_telefono(self, value):
        return normalizar_telefono(value)

    def validate_email(self, value):
        return value.strip().lower()


class ReservaSerializer(serializers.ModelSerializer):
    personas = serializers.IntegerField(min_value=1, max_value=6)
    observaciones = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
    estado = serializers.ChoiceField(choices=Reserva.ESTADOS, required=False)
    noches = serializers.IntegerField(read_only=True)

    class Meta:
        model = Reserva
        fields = ["id", "habitacion", "huesped", "fecha_entrada", "fecha_salida",
                  "personas", "estado", "observaciones", "noches", "total"]
        read_only_fields = ["id", "total", "noches"]

    def validate(self, attrs):
        base = self.instance
        def valor(campo, defecto=None):
            if campo in attrs:
                return attrs[campo]
            return getattr(base, campo) if base else defecto

        estado = valor("estado", Reserva.PENDIENTE)
        if base is None and estado != Reserva.PENDIENTE:
            raise serializers.ValidationError({"estado": "Una reserva nueva siempre empieza como «pendiente»."})
        temporal = Reserva(
            pk=base.pk if base else None,
            habitacion=valor("habitacion"), huesped=valor("huesped"),
            fecha_entrada=valor("fecha_entrada"), fecha_salida=valor("fecha_salida"),
            personas=valor("personas"), estado=estado,
        )
        try:
            temporal.clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        attrs.setdefault("estado", estado)
        return attrs
