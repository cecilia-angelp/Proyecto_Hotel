from django.db import models
from django.core.validators import MinLengthValidator, MinValueValidator

class Habitacion(models.Model):
    numero = models.IntegerField(unique=True, validators=[MinValueValidator(1)], verbose_name="Número de Habitación")
    tipo = models.CharField(max_length=30, validators=[MinLengthValidator(3)], verbose_name="Tipo de Habitación")
    precio = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Precio por Noche")
    disponible = models.BooleanField(default=True, verbose_name="¿Está Disponible?")

    def __str__(self):
        return f"Habitación {self.numero}"