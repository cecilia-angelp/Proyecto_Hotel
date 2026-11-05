from django.db import migrations, models
from django.core.validators import MinLengthValidator, MinValueValidator, MaxValueValidator


class Migration(migrations.Migration):
    dependencies = [("habitaciones", "0001_initial")]
    operations = [
        migrations.AlterField(
            model_name="habitacion",
            name="tipo",
            field=models.CharField(
                max_length=30,
                validators=[MinLengthValidator(3)],
                verbose_name="Tipo de Habitación",
            ),
        ),
        migrations.AlterField(
            model_name="habitacion",
            name="numero",
            field=models.IntegerField(
                unique=True,
                validators=[
                    MinValueValidator(1),
                    MaxValueValidator(2147483647),
                ],
                verbose_name="Número de Habitación",
            ),
        ),
        migrations.AlterField(
            model_name="habitacion",
            name="precio",
            field=models.IntegerField(
                validators=[
                    MinValueValidator(1),
                    MaxValueValidator(9999999),
                ],
                verbose_name="Precio por Noche",
            ),
        ),
    ]
